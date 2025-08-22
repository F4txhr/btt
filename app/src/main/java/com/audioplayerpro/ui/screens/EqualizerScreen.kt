package com.audioplayerpro.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.audioplayerpro.ui.theme.AudioBackground
import com.audioplayerpro.ui.theme.AudioPrimary
import com.audioplayerpro.ui.theme.AudioSurface
import com.audioplayerpro.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EqualizerScreen(
    viewModel: MainViewModel,
    onNavigateBack: () -> Unit
) {
    val graphicEQGains by viewModel.graphicEQGains.collectAsState()
    val isEqualizerEnabled by viewModel.isEqualizerEnabled.collectAsState()
    val isProUser by viewModel.isProUser.collectAsState()
    val freePresets by viewModel.freePresets.collectAsState()
    val proPresets by viewModel.proPresets.collectAsState()

    val frequencies = listOf("31", "62", "125", "250", "500", "1k", "2k", "4k", "8k", "16k")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Equalizer") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = AudioSurface,
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(AudioBackground)
                .padding(padding)
                .verticalScroll(rememberScrollState())
        ) {
            // Enable/Disable Switch
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Equalizer",
                    style = MaterialTheme.typography.titleLarge,
                    color = Color.White,
                    modifier = Modifier.weight(1f)
                )
                Switch(
                    checked = isEqualizerEnabled,
                    onCheckedChange = { viewModel.setEqualizerEnabled(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = AudioPrimary,
                        checkedTrackColor = AudioPrimary.copy(alpha = 0.5f),
                        uncheckedThumbColor = Color.Gray,
                        uncheckedTrackColor = Color.Gray.copy(alpha = 0.5f)
                    )
                )
            }

            // 10-Band Graphic Equalizer
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = AudioSurface)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Graphic Equalizer (10-Band)",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    // Frequency labels
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        frequencies.forEach { freq ->
                            Text(
                                text = freq,
                                style = MaterialTheme.typography.labelSmall,
                                color = Color.White.copy(alpha = 0.7f),
                                textAlign = TextAlign.Center,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // EQ Sliders
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        graphicEQGains.forEachIndexed { index, gain ->
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(
                                    text = "+12",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color.White.copy(alpha = 0.5f)
                                )
                                
                                Slider(
                                    value = gain,
                                    onValueChange = { viewModel.setGraphicEQBand(index, it) },
                                    valueRange = -12f..12f,
                                    modifier = Modifier
                                        .height(200.dp)
                                        .weight(1f),
                                    colors = SliderDefaults.colors(
                                        thumbColor = AudioPrimary,
                                        activeTrackColor = AudioPrimary,
                                        inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                                    )
                                )
                                
                                Text(
                                    text = gain.toInt().toString(),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color.White
                                )
                                
                                Text(
                                    text = "-12",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color.White.copy(alpha = 0.5f)
                                )
                            }
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    // Reset Button
                    Button(
                        onClick = { viewModel.resetGraphicEQ() },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
                    ) {
                        Icon(Icons.Default.Refresh, contentDescription = "Reset")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Reset to Flat")
                    }
                }
            }

            // Parametric Equalizer (Pro Feature)
            if (isProUser) {
                ParametricEqualizerSection()
            } else {
                ProFeatureCard(
                    title = "Parametric Equalizer",
                    description = "Advanced parametric EQ with unlimited bands, low/high shelf filters, and precise frequency control.",
                    icon = Icons.Default.Tune
                )
            }

            // DSP Controls (Pro Feature)
            if (isProUser) {
                DSPControlsSection(viewModel)
            } else {
                ProFeatureCard(
                    title = "Advanced DSP",
                    description = "Preamp, limiter, compressor, and advanced audio processing controls.",
                    icon = Icons.Default.GraphicEq
                )
            }

            // Presets
            PresetsSection(
                freePresets = freePresets,
                proPresets = proPresets,
                isProUser = isProUser,
                onLoadPreset = { viewModel.loadPreset(it) }
            )
        }
    }
}

@Composable
fun ParametricEqualizerSection() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = AudioSurface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "Parametric Equalizer",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "Add custom parametric bands for precise frequency control",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.7f)
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Button(
                onClick = { /* Add parametric band */ },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Band")
                Spacer(modifier = Modifier.width(8.dp))
                Text("Add Parametric Band")
            }
        }
    }
}

@Composable
fun DSPControlsSection(viewModel: MainViewModel) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = AudioSurface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "DSP Controls",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Preamp
            Text(
                text = "Preamp",
                style = MaterialTheme.typography.labelLarge,
                color = Color.White
            )
            Slider(
                value = 1.0f,
                onValueChange = { viewModel.setPreamp(it) },
                valueRange = 0.1f..3.0f,
                modifier = Modifier.fillMaxWidth(),
                colors = SliderDefaults.colors(
                    thumbColor = AudioPrimary,
                    activeTrackColor = AudioPrimary,
                    inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                )
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Limiter Threshold
            Text(
                text = "Limiter Threshold",
                style = MaterialTheme.typography.labelLarge,
                color = Color.White
            )
            Slider(
                value = 0.95f,
                onValueChange = { viewModel.setLimiterThreshold(it) },
                valueRange = 0.1f..1.0f,
                modifier = Modifier.fillMaxWidth(),
                colors = SliderDefaults.colors(
                    thumbColor = AudioPrimary,
                    activeTrackColor = AudioPrimary,
                    inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                )
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Limiter Ratio
            Text(
                text = "Limiter Ratio",
                style = MaterialTheme.typography.labelLarge,
                color = Color.White
            )
            Slider(
                value = 10.0f,
                onValueChange = { viewModel.setLimiterRatio(it) },
                valueRange = 1.0f..20.0f,
                modifier = Modifier.fillMaxWidth(),
                colors = SliderDefaults.colors(
                    thumbColor = AudioPrimary,
                    activeTrackColor = AudioPrimary,
                    inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                )
            )
        }
    }
}

@Composable
fun ProFeatureCard(
    title: String,
    description: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = AudioSurface.copy(alpha = 0.5f))
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                icon,
                contentDescription = title,
                tint = AudioPrimary,
                modifier = Modifier.size(48.dp)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = description,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.7f),
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "PRO FEATURE",
                style = MaterialTheme.typography.labelSmall,
                color = AudioPrimary
            )
        }
    }
}

@Composable
fun PresetsSection(
    freePresets: List<com.audioplayerpro.data.EQPreset>,
    proPresets: List<com.audioplayerpro.data.EQPreset>,
    isProUser: Boolean,
    onLoadPreset: (com.audioplayerpro.data.EQPreset) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = AudioSurface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "Presets",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Free Presets
            Text(
                text = "Free Presets",
                style = MaterialTheme.typography.labelLarge,
                color = Color.White
            )
            
            freePresets.forEach { preset ->
                PresetItem(
                    preset = preset,
                    onClick = { onLoadPreset(preset) }
                )
            }
            
            if (isProUser) {
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    text = "Pro Presets",
                    style = MaterialTheme.typography.labelLarge,
                    color = AudioPrimary
                )
                
                proPresets.forEach { preset ->
                    PresetItem(
                        preset = preset,
                        onClick = { onLoadPreset(preset) },
                        isPro = true
                    )
                }
            }
        }
    }
}

@Composable
fun PresetItem(
    preset: com.audioplayerpro.data.EQPreset,
    onClick: () -> Unit,
    isPro: Boolean = false
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isPro) AudioPrimary.copy(alpha = 0.2f) else Color.White.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = preset.name,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White,
                modifier = Modifier.weight(1f)
            )
            
            if (isPro) {
                Text(
                    text = "PRO",
                    style = MaterialTheme.typography.labelSmall,
                    color = AudioPrimary
                )
            }
            
            IconButton(onClick = onClick) {
                Icon(
                    Icons.Default.PlayArrow,
                    contentDescription = "Load Preset",
                    tint = Color.White
                )
            }
        }
    }
}