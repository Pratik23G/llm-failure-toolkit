#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <mutex>

 // we will build our mutex and it prevents
    // multiple threads from writing error counts at the same time

std:: mutex mtx;

void countErrors(const std::vector<std::string>& chunk, long long& error_count) {
        long long local_error_count = 0;
        for (const auto& line : chunk) {
            if (line.find("error") != std::string::npos) {
                local_error_count++;
            }
        }
        // Lock the mutex before updating the shared error count
        std::lock_guard < std::mutex > lock(mtx);
        error_count += local_error_count;
    }


int main(int argc, char * argv[])
{
    if (argc < 2){
        std:: cerr << "Usage: ./log_processor <path_to_file>\n";
        return 1;
    }

    std:: ifstream inputFile { argv[1] };

    if (! inputFile){
        
        std:: cerr << "Hmm, Sorry I could not find runs.jsonl file! \n";

        return 1;
    }

    std:: string strInput{};

    std::vector<std::string> count_lines_log;
    std::vector<std::string> error_lines_log;

    while(std:: getline(inputFile, strInput)){

        count_lines_log.push_back(strInput);

        if (strInput.find("error") != std:: string::npos){
            error_lines_log.push_back(strInput);
        }
    }

    long long count = count_lines_log.size();
    long long err_count = 0;

    //split into 4 chunks and lauch teh threads
    int num_threads = 4;
    std::vector< std::thread > threads;
    long long chunk_size = count / num_threads;

    for (int i = 0; i< num_threads; i++) {
        long long start = i * chunk_size;
        long long end = (i == num_threads - 1) ? count : start + chunk_size;

        std::vector< std::string > chunk (
            count_lines_log.begin() + start,
            count_lines_log.begin() + end
        );
        threads.push_back(std:: thread(countErrors, chunk, std::ref(err_count)));
    }

    

    // Wait for all threads to complete
    for (auto& t : threads) {
        t.join();
    }

    std:: cout << "Total lines: " << count << std:: endl;
    std:: cout << "Error lines: " << err_count << std:: endl;

    return 0;
}