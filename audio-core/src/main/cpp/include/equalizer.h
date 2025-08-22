#ifndef EQUALIZER_H
#define EQUALIZER_H

#include <vector>
#include <array>

// 10-band graphic equalizer frequencies
const std::array<float, 10> GRAPHIC_EQ_FREQUENCIES = {
    31.25f, 62.5f, 125.0f, 250.0f, 500.0f,
    1000.0f, 2000.0f, 4000.0f, 8000.0f, 16000.0f
};

// Parametric EQ band
struct ParametricBand {
    float frequency;
    float q;
    float gain;
    bool enabled;
};

class Equalizer {
public:
    Equalizer();
    ~Equalizer();

    // Graphic EQ (10-band)
    void setGraphicEQBand(int band, float gain);
    float getGraphicEQBand(int band) const;
    void setGraphicEQBands(const std::array<float, 10>& gains);
    std::array<float, 10> getGraphicEQBands() const;
    void resetGraphicEQ();

    // Parametric EQ
    void addParametricBand(const ParametricBand& band);
    void removeParametricBand(int index);
    void updateParametricBand(int index, const ParametricBand& band);
    void clearParametricBands();

    // Processing
    void processAudio(float* input, float* output, int numFrames, int numChannels);
    void setSampleRate(int sampleRate);

    // Enable/disable
    void setEnabled(bool enabled);
    bool isEnabled() const;

    // Preset management
    void loadPreset(const std::string& name);
    void savePreset(const std::string& name);
    std::vector<std::string> getPresetNames() const;

private:
    std::array<float, 10> graphicEQGains_;
    std::vector<ParametricBand> parametricBands_;
    
    int sampleRate_;
    bool enabled_;
    
    // Filter coefficients for graphic EQ
    struct FilterCoeffs {
        float b0, b1, b2, a1, a2;
    };
    std::array<FilterCoeffs, 10> graphicEQCoeffs_;
    
    // Update filter coefficients
    void updateGraphicEQCoeffs();
    void updateParametricEQCoeffs();
    
    // Apply filters
    void applyGraphicEQ(float* buffer, int numFrames, int numChannels);
    void applyParametricEQ(float* buffer, int numFrames, int numChannels);
    
    // Helper functions for filter design
    FilterCoeffs designLowShelf(float frequency, float gain, float q);
    FilterCoeffs designHighShelf(float frequency, float gain, float q);
    FilterCoeffs designPeaking(float frequency, float gain, float q);
};

#endif // EQUALIZER_H