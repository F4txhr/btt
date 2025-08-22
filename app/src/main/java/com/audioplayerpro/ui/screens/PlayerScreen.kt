package com.audioplayerpro.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.audioplayerpro.ui.theme.AudioBackground
import com.audioplayerpro.ui.theme.AudioPrimary
import com.audioplayerpro.ui.theme.AudioSurface
import com.audioplayerpro.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlayerScreen(
    viewModel: MainViewModel,
    onNavigateToEqualizer: () -> Unit,
    onNavigateToVisualizer: () -> Unit,
    onNavigateToMixer: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    val isPlaying by viewModel.isPlaying.collectAsState()
    val currentTrack by viewModel.currentTrack.collectAsState()
    val volume by viewModel.volume.collectAsState()
    val isProUser by viewModel.isProUser.collectAsState()
    val spectrum by viewModel.spectrum.collectAsState()
    val leftPeak by viewModel.leftPeak.collectAsState()
    val rightPeak by viewModel.rightPeak.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Audio Player Pro") },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = AudioSurface,
                    titleContentColor = Color.White
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(AudioBackground)
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Album Art Placeholder
            Box(
                modifier = Modifier
                    .size(200.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(AudioSurface),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.MusicNote,
                    contentDescription = "Album Art",
                    modifier = Modifier.size(64.dp),
                    tint = Color.White
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Track Info
            currentTrack?.let { track ->
                Text(
                    text = track.name,
                    style = MaterialTheme.typography.headlineSmall,
                    color = Color.White,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = track.artist,
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.White.copy(alpha = 0.7f),
                    textAlign = TextAlign.Center
                )
            } ?: run {
                Text(
                    text = "No track selected",
                    style = MaterialTheme.typography.headlineSmall,
                    color = Color.White,
                    textAlign = TextAlign.Center
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Visualizer
            SpectrumVisualizer(
                spectrum = spectrum,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(100.dp)
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Peak Meters
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                PeakMeter(
                    value = leftPeak,
                    label = "L",
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(16.dp))
                PeakMeter(
                    value = rightPeak,
                    label = "R",
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Playback Controls
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = { /* Previous */ },
                    modifier = Modifier.size(48.dp)
                ) {
                    Icon(
                        Icons.Default.SkipPrevious,
                        contentDescription = "Previous",
                        tint = Color.White,
                        modifier = Modifier.size(32.dp)
                    )
                }

                FloatingActionButton(
                    onClick = { if (isPlaying) viewModel.pause() else viewModel.play() },
                    modifier = Modifier.size(72.dp),
                    containerColor = AudioPrimary
                ) {
                    Icon(
                        if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = if (isPlaying) "Pause" else "Play",
                        modifier = Modifier.size(36.dp),
                        tint = Color.White
                    )
                }

                IconButton(
                    onClick = { /* Next */ },
                    modifier = Modifier.size(48.dp)
                ) {
                    Icon(
                        Icons.Default.SkipNext,
                        contentDescription = "Next",
                        tint = Color.White,
                        modifier = Modifier.size(32.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Volume Control
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.VolumeDown,
                    contentDescription = "Volume",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
                Slider(
                    value = volume,
                    onValueChange = { viewModel.setVolume(it) },
                    modifier = Modifier.weight(1f).padding(horizontal = 16.dp),
                    colors = SliderDefaults.colors(
                        thumbColor = AudioPrimary,
                        activeTrackColor = AudioPrimary,
                        inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                    )
                )
                Icon(
                    Icons.Default.VolumeUp,
                    contentDescription = "Volume",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Feature Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                FeatureButton(
                    icon = Icons.Default.GraphicEq,
                    label = "Equalizer",
                    onClick = onNavigateToEqualizer,
                    isPro = false
                )
                
                FeatureButton(
                    icon = Icons.Default.Analytics,
                    label = "Visualizer",
                    onClick = onNavigateToVisualizer,
                    isPro = false
                )
                
                FeatureButton(
                    icon = Icons.Default.Tune,
                    label = "Mixer",
                    onClick = onNavigateToMixer,
                    isPro = true,
                    isProUser = isProUser
                )
            }
        }
    }
}

@Composable
fun SpectrumVisualizer(
    spectrum: List<Float>,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.Bottom
    ) {
        spectrum.forEach { value ->
            Box(
                modifier = Modifier
                    .weight(1f)
                    .height((value * 100).dp)
                    .background(
                        color = AudioPrimary,
                        shape = RoundedCornerShape(topStart = 2.dp, topEnd = 2.dp)
                    )
            )
        }
    }
}

@Composable
fun PeakMeter(
    value: Float,
    label: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = Color.White
        )
        Spacer(modifier = Modifier.height(4.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(60.dp)
                .background(Color.White.copy(alpha = 0.1f), RoundedCornerShape(4.dp))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height((value * 60).dp)
                    .background(
                        color = if (value > 0.8f) Color.Red else AudioPrimary,
                        shape = RoundedCornerShape(4.dp)
                    )
                    .align(Alignment.BottomCenter)
            )
        }
    }
}

@Composable
fun FeatureButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit,
    isPro: Boolean,
    isProUser: Boolean = false
) {
    val enabled = !isPro || isProUser
    
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        IconButton(
            onClick = onClick,
            enabled = enabled,
            modifier = Modifier.size(56.dp)
        ) {
            Icon(
                icon,
                contentDescription = label,
                tint = if (enabled) Color.White else Color.White.copy(alpha = 0.3f),
                modifier = Modifier.size(32.dp)
            )
        }
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = if (enabled) Color.White else Color.White.copy(alpha = 0.3f)
        )
        if (isPro && !isProUser) {
            Text(
                text = "PRO",
                style = MaterialTheme.typography.labelSmall,
                color = AudioPrimary
            )
        }
    }
}