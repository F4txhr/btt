# Audio Player Pro

A professional Android audio player application with high-resolution audio support, advanced equalizer, real-time visualizer, and AI-powered stem separation capabilities.

## Features

### 🎵 Core Audio Features
- **High-Resolution Audio Playback**: Support for FLAC, WAV, MP3, AAC, OGG, and DSD formats
- **192 kHz, 32-bit Float Output**: Native Oboe/AAudio implementation for maximum audio quality
- **MediaSession Integration**: Lockscreen controls and notification media controls
- **Background Playback**: Continuous audio playback with foreground service

### 🎛️ Equalizer & DSP
- **10-Band Graphic Equalizer**: Real-time frequency adjustment with visual feedback
- **Parametric Equalizer** (Pro): Unlimited custom bands with precise frequency control
- **Advanced DSP Processing**: Preamp, limiter, compressor, and headroom protection
- **EQ Presets**: Save and load custom equalizer configurations
- **Real-time Processing**: Native C++ DSP engine for low-latency audio processing

### 📊 Visualizer
- **FFT Spectrum Analyzer**: 64-band real-time frequency spectrum display
- **Waveform Display**: Real-time audio waveform visualization
- **Peak Meters**: Left/Right channel and RMS level monitoring
- **Smooth Animations**: Hardware-accelerated rendering with 60 FPS updates

### 🎚️ Stem Separation & Mixer (Pro)
- **AI-Powered Separation**: Separate any song into individual stems (Vocals, Drums, Bass, Guitar, Other)
- **Professional Mixer**: Individual volume control for each stem
- **Mute/Solo Controls**: Professional mixing workflow
- **Export Options**: Save mixed stems in WAV or FLAC format
- **Background Processing**: TensorFlow Lite-powered separation using WorkManager

### 💎 Pro Features
- **Parametric Equalizer**: Advanced EQ with unlimited bands
- **Stem Separation**: AI-powered audio separation
- **Advanced DSP**: Professional audio processing tools
- **Export Capabilities**: High-quality audio export
- **Google Play Billing**: Secure in-app purchase integration

## Technical Architecture

### Project Structure
```
AudioPlayerPro/
├── app/                    # Main application module
│   ├── src/main/
│   │   ├── java/com/audioplayerpro/
│   │   │   ├── ui/         # Jetpack Compose UI components
│   │   │   ├── viewmodel/  # ViewModels and state management
│   │   │   ├── data/       # Room database and data models
│   │   │   ├── billing/    # Google Play Billing integration
│   │   │   └── service/    # Background services
│   │   └── res/            # Resources and assets
├── audio-core/             # Native audio processing module
│   ├── src/main/
│   │   ├── cpp/            # C++ native code
│   │   │   ├── include/    # Header files
│   │   │   └── *.cpp       # Implementation files
│   │   └── java/           # JNI wrapper classes
└── audio-ml/               # Machine learning module
    ├── src/main/
    │   ├── java/           # TensorFlow Lite integration
    │   └── assets/         # ML models
```

### Key Technologies

#### Native Audio Processing
- **Oboe**: High-performance audio I/O library
- **C++17**: Modern C++ for audio processing
- **CMake**: Native build system
- **JNI**: Java-Native Interface for Kotlin integration

#### Audio Processing Features
- **IIR Filters**: Real-time digital signal processing
- **FFT Analysis**: Fast Fourier Transform for spectrum analysis
- **High-Resolution Audio**: 192 kHz, 32-bit float processing
- **Low Latency**: Optimized for real-time audio applications

#### Machine Learning
- **TensorFlow Lite**: On-device AI inference
- **Spleeter Model**: Pre-trained stem separation model
- **WorkManager**: Background processing for ML tasks
- **Model Optimization**: Quantized models for mobile deployment

#### UI & Architecture
- **Jetpack Compose**: Modern declarative UI toolkit
- **Material 3**: Latest Material Design components
- **MVVM Architecture**: Clean architecture with ViewModels
- **Room Database**: Local data persistence
- **Navigation Compose**: Type-safe navigation

## Installation & Setup

### Prerequisites
- Android Studio Arctic Fox or later
- Android SDK 24+ (API level 24)
- NDK 25.0+ for native development
- CMake 3.22.1+ for native builds

### Build Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AudioPlayerPro.git
   cd AudioPlayerPro
   ```

2. **Open in Android Studio**
   - Open Android Studio
   - Select "Open an existing project"
   - Navigate to the cloned directory and select it

3. **Sync and Build**
   - Wait for Gradle sync to complete
   - Build the project (Build → Make Project)
   - Run on device or emulator

### Configuration

#### Google Play Billing Setup
1. Create a Google Play Console account
2. Set up in-app products:
   - `audioplayer_pro` (lifetime purchase)
   - `audioplayer_pro_monthly` (subscription)
   - `audioplayer_pro_yearly` (subscription)
3. Update billing configuration in `BillingManager.kt`

#### ML Model Setup
1. Download the Spleeter model files
2. Place them in `audio-ml/src/main/assets/`
3. Update model paths in `StemSeparationService.kt`

## Usage

### Basic Audio Playback
1. Launch the app
2. Grant storage permissions when prompted
3. Use the main player interface to control playback
4. Adjust volume using the slider

### Equalizer
1. Navigate to the Equalizer screen
2. Enable the equalizer using the toggle
3. Adjust the 10-band graphic equalizer sliders
4. Save custom presets for later use

### Visualizer
1. Navigate to the Visualizer screen
2. View real-time spectrum analyzer and waveform
3. Monitor audio levels with peak meters
4. Adjust visualization settings

### Stem Separation (Pro)
1. Upgrade to Pro version
2. Navigate to the Mixer screen
3. Select an audio file for separation
4. Wait for AI processing to complete
5. Mix individual stems using the mixer controls
6. Export the final mix

## Development

### Adding New Audio Formats
1. Update `AudioEngine.cpp` to handle new formats
2. Add format detection in `AudioPlayerNative.kt`
3. Update UI to display format information

### Custom DSP Effects
1. Implement new effects in `DSPProcessor.cpp`
2. Add effect parameters to `EffectParams` struct
3. Update UI controls in equalizer screen

### ML Model Integration
1. Convert models to TensorFlow Lite format
2. Update `StemSeparationService.kt` for new models
3. Test performance on target devices

## Performance Optimization

### Audio Latency
- Use Oboe's low-latency mode
- Optimize DSP algorithms for real-time processing
- Minimize JNI calls between Java and native code

### Memory Management
- Use object pooling for audio buffers
- Implement proper cleanup in native code
- Monitor memory usage during ML processing

### Battery Optimization
- Implement efficient FFT algorithms
- Use WorkManager for background tasks
- Optimize UI updates for smooth performance

## Troubleshooting

### Common Issues

#### Build Errors
- **NDK not found**: Install NDK through SDK Manager
- **CMake errors**: Update CMake version in project settings
- **Native library linking**: Check library paths in CMakeLists.txt

#### Runtime Issues
- **Audio not playing**: Check device audio settings and permissions
- **High latency**: Verify Oboe configuration and buffer sizes
- **ML processing fails**: Ensure model files are properly included

#### Performance Issues
- **UI lag**: Reduce visualizer update frequency
- **Audio dropouts**: Increase audio buffer size
- **Memory leaks**: Check native code cleanup

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow Kotlin coding conventions
- Use meaningful variable and function names
- Add comments for complex algorithms
- Include unit tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Oboe**: Google's high-performance audio library
- **TensorFlow Lite**: On-device machine learning framework
- **Spleeter**: Deezer's open-source audio separation library
- **Jetpack Compose**: Modern Android UI toolkit
- **Material Design**: Google's design system

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**Audio Player Pro** - Professional audio processing on Android