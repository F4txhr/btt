#include "visualizer.h"
#include <algorithm>
#include <cmath>
#include <complex>

Visualizer::Visualizer()
    : sampleRate_(48000)
    , smoothing_(0.8f)
    , windowType_(1) // Hanning window
    , enabled_(false)
    , leftPeak_(0.0f)
    , rightPeak_(0.0f)
    , rms_(0.0f) {
    
    // Initialize buffers
    fftBuffer_.resize(FFT_SIZE);
    fftOutput_.resize(FFT_SIZE);
    waveform_.resize(FFT_SIZE);
    spectrum_.fill(0.0f);
}

Visualizer::~Visualizer() {
}

void Visualizer::processAudio(const float* input, int numFrames, int numChannels) {
    if (!enabled_) return;

    // Update peak levels
    updatePeaks(input, numFrames, numChannels);

    // Update waveform buffer (simple circular buffer)
    static int waveformIndex = 0;
    for (int i = 0; i < numFrames && i < FFT_SIZE; ++i) {
        float sample = 0.0f;
        for (int ch = 0; ch < numChannels; ++ch) {
            sample += input[i * numChannels + ch];
        }
        sample /= numChannels; // Average across channels
        
        waveform_[waveformIndex] = sample;
        waveformIndex = (waveformIndex + 1) % FFT_SIZE;
    }

    // Update FFT buffer
    for (int i = 0; i < FFT_SIZE; ++i) {
        fftBuffer_[i] = waveform_[i];
    }

    // Perform FFT analysis
    performFFT();
}

const std::array<float, SPECTRUM_BANDS>& Visualizer::getSpectrum() const {
    return spectrum_;
}

const std::vector<float>& Visualizer::getWaveform() const {
    return waveform_;
}

float Visualizer::getLeftPeak() const {
    return leftPeak_;
}

float Visualizer::getRightPeak() const {
    return rightPeak_;
}

float Visualizer::getRMS() const {
    return rms_;
}

void Visualizer::setSampleRate(int sampleRate) {
    sampleRate_ = sampleRate;
}

void Visualizer::setSmoothing(float smoothing) {
    smoothing_ = std::clamp(smoothing, 0.0f, 1.0f);
}

void Visualizer::setWindowType(int windowType) {
    windowType_ = windowType;
}

void Visualizer::setEnabled(bool enabled) {
    enabled_ = enabled;
}

bool Visualizer::isEnabled() const {
    return enabled_;
}

void Visualizer::performFFT() {
    // Apply window function
    applyWindow(fftBuffer_.data());

    // Simple FFT implementation (using complex numbers)
    // This is a basic radix-2 FFT - for production use, consider using FFTW or similar
    int n = FFT_SIZE;
    
    // Bit-reversal permutation
    for (int i = 0; i < n; ++i) {
        int j = 0;
        int temp = i;
        for (int k = 0; k < 16; ++k) { // Assuming FFT_SIZE <= 65536
            j = (j << 1) | (temp & 1);
            temp >>= 1;
        }
        if (j < i) {
            std::swap(fftBuffer_[i], fftBuffer_[j]);
        }
    }

    // FFT computation
    for (int step = 1; step < n; step <<= 1) {
        float angle = -M_PI / step;
        std::complex<float> w(1.0f, 0.0f);
        std::complex<float> wn(std::cos(angle), std::sin(angle));

        for (int group = 0; group < n; group += 2 * step) {
            std::complex<float> w_temp(1.0f, 0.0f);
            
            for (int pair = group; pair < group + step; ++pair) {
                std::complex<float> temp = w_temp * std::complex<float>(fftBuffer_[pair + step], 0.0f);
                fftOutput_[pair] = std::complex<float>(fftBuffer_[pair], 0.0f) + temp;
                fftOutput_[pair + step] = std::complex<float>(fftBuffer_[pair], 0.0f) - temp;
                w_temp *= wn;
            }
        }
        
        // Copy back to input buffer
        for (int i = 0; i < n; ++i) {
            fftBuffer_[i] = fftOutput_[i].real();
        }
    }

    // Calculate spectrum
    calculateSpectrum();
}

void Visualizer::applyWindow(float* buffer) {
    for (int i = 0; i < FFT_SIZE; ++i) {
        float window = 1.0f;
        
        switch (windowType_) {
            case 1: // Hanning window
                window = 0.5f * (1.0f - std::cos(2.0f * M_PI * i / (FFT_SIZE - 1)));
                break;
            case 2: // Hamming window
                window = 0.54f - 0.46f * std::cos(2.0f * M_PI * i / (FFT_SIZE - 1));
                break;
            default: // Rectangular window
                window = 1.0f;
                break;
        }
        
        buffer[i] *= window;
    }
}

void Visualizer::calculateSpectrum() {
    // Group FFT bins into frequency bands
    int binsPerBand = FFT_SIZE / 2 / SPECTRUM_BANDS;
    
    for (int band = 0; band < SPECTRUM_BANDS; ++band) {
        float magnitude = 0.0f;
        int startBin = band * binsPerBand;
        int endBin = startBin + binsPerBand;
        
        for (int bin = startBin; bin < endBin && bin < FFT_SIZE / 2; ++bin) {
            float real = fftBuffer_[bin];
            float imag = (bin < FFT_SIZE / 2) ? fftBuffer_[bin + FFT_SIZE / 2] : 0.0f;
            float mag = std::sqrt(real * real + imag * imag);
            magnitude = std::max(magnitude, mag);
        }
        
        // Convert to dB
        float db = 20.0f * std::log10(magnitude + 1e-10f);
        db = std::clamp(db, -60.0f, 0.0f);
        
        // Apply smoothing
        spectrum_[band] = smoothing_ * spectrum_[band] + (1.0f - smoothing_) * (db + 60.0f) / 60.0f;
    }
}

void Visualizer::smoothSpectrum() {
    // Additional smoothing if needed
    std::array<float, SPECTRUM_BANDS> temp = spectrum_;
    
    for (int i = 0; i < SPECTRUM_BANDS; ++i) {
        float sum = temp[i];
        int count = 1;
        
        if (i > 0) {
            sum += temp[i - 1];
            count++;
        }
        if (i < SPECTRUM_BANDS - 1) {
            sum += temp[i + 1];
            count++;
        }
        
        spectrum_[i] = sum / count;
    }
}

float Visualizer::calculateRMS(const float* buffer, int size) {
    float sum = 0.0f;
    for (int i = 0; i < size; ++i) {
        sum += buffer[i] * buffer[i];
    }
    return std::sqrt(sum / size);
}

void Visualizer::updatePeaks(const float* buffer, int numFrames, int numChannels) {
    float leftMax = 0.0f;
    float rightMax = 0.0f;
    float sum = 0.0f;
    
    for (int i = 0; i < numFrames; ++i) {
        if (numChannels >= 1) {
            float left = std::abs(buffer[i * numChannels]);
            leftMax = std::max(leftMax, left);
        }
        if (numChannels >= 2) {
            float right = std::abs(buffer[i * numChannels + 1]);
            rightMax = std::max(rightMax, right);
        }
        
        // Calculate RMS
        for (int ch = 0; ch < numChannels; ++ch) {
            sum += buffer[i * numChannels + ch] * buffer[i * numChannels + ch];
        }
    }
    
    // Apply smoothing to peaks
    float smoothing = 0.95f;
    leftPeak_ = smoothing * leftPeak_ + (1.0f - smoothing) * leftMax;
    rightPeak_ = smoothing * rightPeak_ + (1.0f - smoothing) * rightMax;
    
    // Calculate RMS
    rms_ = std::sqrt(sum / (numFrames * numChannels));
}