#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <map>
#include <algorithm>
#include <numeric>
#include <sstream>
#include "json.hpp"
using json = nlohmann::json;

// ── Step 1: Define the struct FIRST before anything uses it ──────────────────
// C++ reads top to bottom — global_stats uses AgentStats, so this must come first
struct AgentStats {
    long long total        = 0;
    long long error_count  = 0;
    long long val_failed   = 0;
    long long null_resp    = 0;
    std::vector<double> latencies;
};

// ── Step 2: Now we can declare globals that use AgentStats ───────────────────
std::mutex mtx;
std::map<std::string, AgentStats> global_stats;

// ── Helper 1: Extract latency in ms regardless of which field name was used ──
// Your logs changed field names 3 times across your project history
double extract_latency_ms(const json& j) {
    if (j.contains("fan_out_latency_sec") && j["fan_out_latency_sec"].is_number())
        return j["fan_out_latency_sec"].get<double>() * 1000.0; // convert seconds -> ms

    if (j.contains("latency_ms") && j["latency_ms"].is_number())
        return j["latency_ms"].get<double>();

    if (j.contains("latency(ms) ") && j["latency(ms) "].is_number()) // note the trailing space
        return j["latency(ms) "].get<double>();

    return -1.0; // -1 means field not found
}

// ── Helper 2: Decide if a log entry represents a failure ─────────────────────
bool is_error(const json& j) {
    // Newer logs have error_meta.ok — most reliable
    if (j.contains("error_meta") && j["error_meta"].is_object()) {
        auto& em = j["error_meta"];
        if (em.contains("ok") && em["ok"].is_boolean())
            return !em["ok"].get<bool>();
    }
    // Older logs fall back to validation.passed
    if (j.contains("validation") && j["validation"].is_object()) {
        auto& v = j["validation"];
        if (v.contains("passed") && v["passed"].is_boolean())
            return !v["passed"].get<bool>();
    }
    return false;
}

// ── Helper 3: Compute a percentile from a vector of values ───────────────────
// p=50 gives median, p=95 gives p95, etc.
double percentile(std::vector<double>& v, double p) {
    if (v.empty()) return 0.0;
    std::sort(v.begin(), v.end());
    size_t idx = static_cast<size_t>(p / 100.0 * (v.size() - 1));
    return v[idx];
}

// ── Thread worker: processes one chunk of lines ───────────────────────────────
void process_chunk(const std::vector<std::string>& chunk) {
    // Local map — no lock needed while building this
    std::map<std::string, AgentStats> local_stats;

    for (const auto& line : chunk) {
        if (line.empty()) continue;

        json j;
        try {
            j = json::parse(line);
        } catch (...) {
            continue; // skip malformed lines — don't crash
        }

        // Get model name, default to "unknown" if missing
        std::string model = "unknown";
        if (j.contains("model_name") && j["model_name"].is_string())
            model = j["model_name"].get<std::string>();

        AgentStats& s = local_stats[model]; // & = reference, modifies the map entry directly
        s.total++;

        double lat = extract_latency_ms(j);
        if (lat >= 0.0)
            s.latencies.push_back(lat);

        if (is_error(j))
            s.error_count++;

        if (j.contains("validation") && j["validation"].is_object()) {
            auto& v = j["validation"];
            if (v.contains("passed") && v["passed"].is_boolean())
                if (!v["passed"].get<bool>())
                    s.val_failed++;
        }

        if (j.contains("ai_response")) {
            auto& r = j["ai_response"];
            if (r.is_null())
                s.null_resp++;
            else if (r.is_string() && r.get<std::string>().empty())
                s.null_resp++;
        }
    }

    // ONE lock per chunk — merge local results into global
    std::lock_guard<std::mutex> lock(mtx);
    for (auto& [model, ls] : local_stats) {
        auto& gs = global_stats[model];
        gs.total       += ls.total;
        gs.error_count += ls.error_count;
        gs.val_failed  += ls.val_failed;
        gs.null_resp   += ls.null_resp;
        gs.latencies.insert(gs.latencies.end(),
                            ls.latencies.begin(), ls.latencies.end());
    }
}

// ── Output: prints structured JSON to stdout ──────────────────────────────────
// Python can do: json.loads(subprocess.check_output(["./log_processor", "file"]))
void emit_json(long long total_lines) {
    json out;
    out["total_lines"] = total_lines;

    long long total_errors   = 0;
    long long total_val_fail = 0;

    json agents = json::object();
    for (auto& [model, s] : global_stats) {
        total_errors   += s.error_count;
        total_val_fail += s.val_failed;

        double avg = 0.0;
        if (!s.latencies.empty())
            avg = std::accumulate(s.latencies.begin(), s.latencies.end(), 0.0)
                  / s.latencies.size();

        double err_rate = s.total > 0 ? 100.0 * s.error_count / s.total : 0.0;

        agents[model] = {
            {"total",           s.total},
            {"errors",          s.error_count},
            {"error_rate_pct",  err_rate},
            {"val_failed",      s.val_failed},
            {"null_responses",  s.null_resp},
            {"avg_latency_ms",  avg},
            {"p50_latency_ms",  percentile(s.latencies, 50.0)},
            {"p95_latency_ms",  percentile(s.latencies, 95.0)},
            {"p99_latency_ms",  percentile(s.latencies, 99.0)},
        };
    }

    out["total_errors"]           = total_errors;
    out["total_validation_fails"] = total_val_fail;
    out["errors_by_agent"]        = agents;

    std::cout << out.dump(2) << std::endl;
}

// ── main ──────────────────────────────────────────────────────────────────────
int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: ./log_processor <path_to_file>\n";
        return 1;
    }

    std::ifstream inputFile(argv[1]);
    if (!inputFile) {
        std::cerr << "Sorry, could not open file!\n";
        return 1;
    }

    // Read all lines into memory first (fast sequential I/O)
    std::vector<std::string> lines;
    std::string line;
    while (std::getline(inputFile, line))
        lines.push_back(std::move(line));

    long long total = static_cast<long long>(lines.size());
    if (total == 0) {
        std::cerr << "File is empty.\n";
        return 1;
    }

    // Split into chunks and launch threads
    const int NUM_THREADS = 4;
    std::vector<std::thread> threads;
    long long chunk_size = total / NUM_THREADS;

    for (int i = 0; i < NUM_THREADS; i++) {
        long long start = i * chunk_size;
        long long end   = (i == NUM_THREADS - 1) ? total : start + chunk_size;

        std::vector<std::string> chunk(
            lines.begin() + start,
            lines.begin() + end
        );
        threads.emplace_back(process_chunk, std::move(chunk));
    }

    for (auto& t : threads)
        t.join();

    emit_json(total);
    return 0;
}