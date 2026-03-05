#include <iostream>
#include <fstream>
#include <string>

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

    int count = 0;

    while(std:: getline(inputFile, strInput)){

        count++;
    }

    std:: cout << count << std:: endl;

    return 0;
}