#ifndef VISUALIZER_H
#define VISUALIZER_H

#include <vector>
#include <complex>
#include <array>

// FFT size for spectrum analysis
constexpr int FFT_SIZE = 2048;
constexpr int SPECTRUM_BANDS = 64;

class Visualizer {
public:
    Visualizer();
    ~Visualizer();

    // Process audio data for visualization
    void processAudio(const float* input, int numFrames, int numChannels);

    // Get spectrum data (magnitude in dB)
    const std::array<float, SPECTRUM_BANDS>& getSpectrum() const;
    
    // Get waveform data
    const std::vector<float>& getWaveform() const;
    
    // Get peak levels
    float getLeftPeak() const;
    float getRightPeak() const;
    float getRMS() const;

    // Settings
    void setSampleRate(int sampleRate);
    void setSmoothing(float smoothing); // 0.0 to 1.0
    void setWindowType(int windowType); // 0=Rectangular, 1=Hanning, 2=Hamming

    // Enable/disable
    void setEnabled(bool enabled);
    bool isEnabled() const;

private:
    std::array<float, SPECTRUM_BANDS> spectrum_;
    std::vector<float> waveform_;
    std::vector<float> fftBuffer_;
    std::vector<std::complex<float>> fftOutput_;
    
    int sampleRate_;
    float smoothing_;
    int windowType_;
    bool enabled_;
    
    // Peak detection
    float leftPeak_;
    float rightPeak_;
    float rms_;
    
    // FFT processing
    void performFFT();
    void applyWindow(float* buffer);
    void calculateSpectrum();
    void smoothSpectrum();
    
    // Helper functions
    float calculateRMS(const float* buffer, int size);
    void updatePeaks(const float* buffer, int numFrames, int numChannels);
};

#endif // VISUALIZER_H