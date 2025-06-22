#include <iostream>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <cctype>
#include <sstream>
#include <curl/curl.h>
#include <gumbo.h>

// Write callback for libcurl
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    output->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Fetch HTML from URL
std::string fetch_url(const std::string& url) {
    CURL* curl = curl_easy_init();
    std::string response;

    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);

        CURLcode res = curl_easy_perform(curl);
        if (res != CURLE_OK)
            std::cerr << "Curl error: " << curl_easy_strerror(res) << std::endl;

        curl_easy_cleanup(curl);
    }

    return response;
}

// Recursively extract text from HTML using Gumbo
void extract_text(GumboNode* node, std::string& out_text) {
    if (node->type == GUMBO_NODE_TEXT) {
        out_text += node->v.text.text;
        out_text += " ";
    } else if (node->type == GUMBO_NODE_ELEMENT &&
               node->v.element.tag != GUMBO_TAG_SCRIPT &&
               node->v.element.tag != GUMBO_TAG_STYLE) {
        GumboVector* children = &node->v.element.children;
        for (unsigned int i = 0; i < children->length; ++i) {
            extract_text(static_cast<GumboNode*>(children->data[i]), out_text);
        }
    }
}

// Helper to clean and tokenize text
std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> words;
    std::stringstream ss(text);
    std::string word;

    while (ss >> word) {
        std::string clean;
        for (char c : word) {
            if (std::isalpha(c))
                clean += std::tolower(c);
        }
        if (!clean.empty())
            words.push_back(clean);
    }

    return words;
}

// Count word frequency
std::map<std::string, int> count_words(const std::vector<std::string>& words) {
    std::map<std::string, int> freq;
    for (const auto& word : words)
        ++freq[word];
    return freq;
}

// Sort and get top N frequent words
std::vector<std::pair<std::string, int>> get_top_words(const std::map<std::string, int>& freq, size_t top_n = 10) {
    std::vector<std::pair<std::string, int>> sorted(freq.begin(), freq.end());
    std::sort(sorted.begin(), sorted.end(), [](auto& a, auto& b) {
        return b.second < a.second;
    });
    if (sorted.size() > top_n)
        sorted.resize(top_n);
    return sorted;
}

int main() {
    std::string url = "https://en.wikipedia.org/wiki/Python_(programming_language)";
    std::string html = fetch_url(url);

    if (html.empty()) {
        std::cerr << "Failed to retrieve page content." << std::endl;
        return 1;
    }

    GumboOutput* output = gumbo_parse(html.c_str());
    std::string text;
    extract_text(output->root, text);
    gumbo_destroy_output(&kGumboDefaultOptions, output);

    std::vector<std::string> words = tokenize(text);
    auto word_counts = count_words(words);
    auto top_words = get_top_words(word_counts);

    std::cout << "\nTop 10 Most Common Words:\n";
    for (const auto& [word, count] : top_words) {
        std::cout << word << ": " << count << "\n";
    }

    return 0;
}

//g++ cPlusPlus.cpp -o cPlusPlus -lcurl -lgumbo && ./cPlusPlus

