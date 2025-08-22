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
fun MixerScreen(
    viewModel: MainViewModel,
    onNavigateBack: () -> Unit
) {
    val isProUser by viewModel.isProUser.collectAsState()
    
    var selectedFile by remember { mutableStateOf<String?>(null) }
    var isProcessing by remember { mutableStateOf(false) }
    var processingProgress by remember { mutableStateOf(0f) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Stem Mixer") },
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
            if (isProUser) {
                // File Selection
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
                            text = "Select Audio File",
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.White
                        )
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Button(
                            onClick = { /* Open file picker */ },
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
                        ) {
                            Icon(Icons.Default.FileOpen, contentDescription = "Select File")
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Choose Audio File")
                        }
                        
                        selectedFile?.let { file ->
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "Selected: $file",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color.White.copy(alpha = 0.7f)
                            )
                        }
                    }
                }

                // Processing Section
                if (selectedFile != null) {
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
                                text = "Stem Separation",
                                style = MaterialTheme.typography.titleMedium,
                                color = Color.White
                            )
                            
                            Spacer(modifier = Modifier.height(16.dp))
                            
                            if (isProcessing) {
                                LinearProgressIndicator(
                                    progress = processingProgress,
                                    modifier = Modifier.fillMaxWidth(),
                                    color = AudioPrimary
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    text = "Processing... ${(processingProgress * 100).toInt()}%",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Color.White
                                )
                            } else {
                                Button(
                                    onClick = {
                                        isProcessing = true
                                        // Start stem separation
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
                                ) {
                                    Icon(Icons.Default.PlayArrow, contentDescription = "Start Processing")
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Separate Stems")
                                }
                            }
                        }
                    }
                }

                // Mixer Controls
                StemMixerControls()
                
                // Export Section
                ExportSection()
                
            } else {
                // Pro Feature Card
                ProFeatureCard(
                    title = "Stem Separation & Mixer",
                    description = "Separate any song into individual stems (vocals, drums, bass, guitar, other) and mix them with professional controls.",
                    icon = Icons.Default.Tune
                )
            }
        }
    }
}

@Composable
fun StemMixerControls() {
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
                text = "Stem Mixer",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Vocals
            StemControl(
                name = "Vocals",
                icon = Icons.Default.Mic,
                color = Color.Red
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Drums
            StemControl(
                name = "Drums",
                icon = Icons.Default.Percussion,
                color = Color.Blue
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Bass
            StemControl(
                name = "Bass",
                icon = Icons.Default.MusicNote,
                color = Color.Green
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Guitar
            StemControl(
                name = "Guitar",
                icon = Icons.Default.MusicNote,
                color = Color.Yellow
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Other
            StemControl(
                name = "Other",
                icon = Icons.Default.MusicNote,
                color = Color.Magenta
            )
        }
    }
}

@Composable
fun StemControl(
    name: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color
) {
    var volume by remember { mutableStateOf(1.0f) }
    var isMuted by remember { mutableStateOf(false) }
    var isSolo by remember { mutableStateOf(false) }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color.White.copy(alpha = 0.1f))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Icon
            Icon(
                icon,
                contentDescription = name,
                tint = color,
                modifier = Modifier.size(24.dp)
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            // Name
            Text(
                text = name,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White,
                modifier = Modifier.weight(1f)
            )
            
            // Mute Button
            IconButton(
                onClick = { isMuted = !isMuted },
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    if (isMuted) Icons.Default.VolumeOff else Icons.Default.VolumeUp,
                    contentDescription = if (isMuted) "Unmute" else "Mute",
                    tint = if (isMuted) Color.Red else Color.White
                )
            }
            
            // Solo Button
            IconButton(
                onClick = { isSolo = !isSolo },
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    Icons.Default.Headphones,
                    contentDescription = if (isSolo) "Unsolo" else "Solo",
                    tint = if (isSolo) AudioPrimary else Color.White
                )
            }
            
            Spacer(modifier = Modifier.width(8.dp))
            
            // Volume Slider
            Slider(
                value = if (isMuted) 0f else volume,
                onValueChange = { volume = it },
                enabled = !isMuted,
                modifier = Modifier.width(100.dp),
                colors = SliderDefaults.colors(
                    thumbColor = color,
                    activeTrackColor = color,
                    inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                )
            )
            
            Spacer(modifier = Modifier.width(8.dp))
            
            // Volume Display
            Text(
                text = "${(volume * 100).toInt()}%",
                style = MaterialTheme.typography.labelSmall,
                color = Color.White,
                modifier = Modifier.width(40.dp),
                textAlign = TextAlign.End
            )
        }
    }
}

@Composable
fun ExportSection() {
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
                text = "Export",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                Button(
                    onClick = { /* Export as WAV */ },
                    colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
                ) {
                    Icon(Icons.Default.Download, contentDescription = "Export WAV")
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("WAV")
                }
                
                Button(
                    onClick = { /* Export as FLAC */ },
                    colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
                ) {
                    Icon(Icons.Default.Download, contentDescription = "Export FLAC")
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("FLAC")
                }
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "Export your mixed stems in high-quality formats",
                style = MaterialTheme.typography.bodySmall,
                color = Color.White.copy(alpha = 0.7f),
                textAlign = TextAlign.Center
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
            modifier = Modifier.padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                icon,
                contentDescription = title,
                tint = AudioPrimary,
                modifier = Modifier.size(64.dp)
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = title,
                style = MaterialTheme.typography.headlineSmall,
                color = Color.White,
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = description,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.7f),
                textAlign = TextAlign.Center
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            Text(
                text = "PRO FEATURE",
                style = MaterialTheme.typography.labelMedium,
                color = AudioPrimary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Button(
                onClick = { /* Navigate to Pro purchase */ },
                colors = ButtonDefaults.buttonColors(containerColor = AudioPrimary)
            ) {
                Icon(Icons.Default.Star, contentDescription = "Upgrade to Pro")
                Spacer(modifier = Modifier.width(8.dp))
                Text("Upgrade to Pro")
            }
        }
    }
}