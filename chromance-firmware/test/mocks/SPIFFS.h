#ifndef SPIFFS_H
#define SPIFFS_H

#include <string>
#include <iostream>
#include <fstream>
#include <sys/stat.h>
#include <ArduinoJson.h>

// Simple Mock for SPIFFS FILE
class File {
public:
    std::fstream fs;
    std::string path;
    bool writeMode;

    File() : writeMode(false) {}
    
    File(const std::string& p, const char* mode) : path(p) {
        if (std::string(mode) == "w") {
            writeMode = true;
            fs.open(path, std::ios::out | std::ios::trunc);
        } else {
            writeMode = false;
            fs.open(path, std::ios::in);
        }
    }

    operator bool() {
        return fs.is_open();
    }

    void close() {
        if (fs.is_open()) fs.close();
    }

    size_t write(uint8_t c) {
        fs.put((char)c);
        return 1;
    }

    size_t write(const uint8_t *buf, size_t size) {
        fs.write((const char*)buf, size);
        return size;
    }

    int read() {
        return fs.get();
    }

    size_t read(uint8_t* buf, size_t size) {
        fs.read((char*)buf, size);
        return fs.gcount();
    }
    
    int available() {
        if (!fs.is_open()) return 0;
        std::streampos curr = fs.tellg();
        fs.seekg(0, std::ios::end);
        std::streampos end = fs.tellg();
        fs.seekg(curr, std::ios::beg);
        return (int)(end - curr);
    }
};

// Mock SPIFFS Class
class SPIFFSFS {
public:
    bool begin(bool formatOnFail = false) {
        // Ensure tmp dir exists
        mkdir("tmp_spiffs", 0777);
        return true;
    }

    bool exists(const char* path) {
        std::string p = "tmp_spiffs" + std::string(path);
        struct stat buffer;
        return (stat(p.c_str(), &buffer) == 0);
    }

    File open(const char* path, const char* mode) {
        std::string p = "tmp_spiffs" + std::string(path);
        return File(p, mode);
    }
};

extern SPIFFSFS SPIFFS;

#define FILE_WRITE "w"
#define FILE_READ "r"

#endif
