package com.audioplayerpro.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.unit.dp
import com.audioplayerpro.ui.theme.AudioBackground
import com.audioplayerpro.ui.theme.AudioPrimary
import com.audioplayerpro.ui.theme.AudioSurface
import com.audioplayerpro.ui.theme.VisualizerPrimary
import com.audioplayerpro.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VisualizerScreen(
    viewModel: MainViewModel,
    onNavigateBack: () -> Unit
) {
    val spectrum by viewModel.spectrum.collectAsState()
    val waveform by viewModel.waveform.collectAsState()
    val leftPeak by viewModel.leftPeak.collectAsState()
    val rightPeak by viewModel.rightPeak.collectAsState()
    val rms by viewModel.rms.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Visualizer") },
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
                .padding(16.dp)
        ) {
            // Spectrum Analyzer
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(300.dp)
                    .padding(bottom = 16.dp),
                colors = CardDefaults.cardColors(containerColor = AudioSurface)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Spectrum Analyzer",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color.Black, RoundedCornerShape(8.dp))
                    ) {
                        SpectrumAnalyzer(
                            spectrum = spectrum,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                }
            }

            // Waveform Display
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
                    .padding(bottom = 16.dp),
                colors = CardDefaults.cardColors(containerColor = AudioSurface)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Waveform",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color.Black, RoundedCornerShape(8.dp))
                    ) {
                        WaveformDisplay(
                            waveform = waveform,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                }
            }

            // Audio Meters
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                // Left Channel Meter
                AudioMeter(
                    value = leftPeak,
                    label = "Left",
                    modifier = Modifier.weight(1f)
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                // Right Channel Meter
                AudioMeter(
                    value = rightPeak,
                    label = "Right",
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // RMS Meter
            AudioMeter(
                value = rms,
                label = "RMS",
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Visualizer Settings
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = AudioSurface)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Visualizer Settings",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Smoothing",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color.White,
                            modifier = Modifier.weight(1f)
                        )
                        Slider(
                            value = 0.8f,
                            onValueChange = { /* Update smoothing */ },
                            modifier = Modifier.weight(1f),
                            colors = SliderDefaults.colors(
                                thumbColor = AudioPrimary,
                                activeTrackColor = AudioPrimary,
                                inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                            )
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Sensitivity",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color.White,
                            modifier = Modifier.weight(1f)
                        )
                        Slider(
                            value = 0.5f,
                            onValueChange = { /* Update sensitivity */ },
                            modifier = Modifier.weight(1f),
                            colors = SliderDefaults.colors(
                                thumbColor = AudioPrimary,
                                activeTrackColor = AudioPrimary,
                                inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                            )
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SpectrumAnalyzer(
    spectrum: List<Float>,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height
        val barWidth = width / spectrum.size
        
        spectrum.forEachIndexed { index, value ->
            val barHeight = value * height
            val x = index * barWidth
            val y = height - barHeight
            
            // Create gradient for each bar
            val brush = Brush.verticalGradient(
                colors = listOf(
                    VisualizerPrimary,
                    VisualizerPrimary.copy(alpha = 0.7f),
                    VisualizerPrimary.copy(alpha = 0.3f)
                ),
                startY = y,
                endY = height
            )
            
            drawRect(
                brush = brush,
                topLeft = Offset(x + 1, y),
                size = androidx.compose.ui.geometry.Size(barWidth - 2, barHeight)
            )
        }
    }
}

@Composable
fun WaveformDisplay(
    waveform: List<Float>,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height
        val centerY = height / 2
        
        if (waveform.isNotEmpty()) {
            val path = Path()
            val stepX = width / (waveform.size - 1)
            
            waveform.forEachIndexed { index, value ->
                val x = index * stepX
                val y = centerY + (value * centerY)
                
                if (index == 0) {
                    path.moveTo(x, y)
                } else {
                    path.lineTo(x, y)
                }
            }
            
            drawPath(
                path = path,
                brush = Brush.horizontalGradient(
                    colors = listOf(
                        VisualizerPrimary,
                        AudioPrimary,
                        VisualizerPrimary
                    )
                ),
                style = Stroke(width = 2f)
            )
        }
    }
}

@Composable
fun AudioMeter(
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
                .height(120.dp)
                .background(Color.White.copy(alpha = 0.1f), RoundedCornerShape(4.dp))
        ) {
            // Background segments
            repeat(20) { segment ->
                val segmentHeight = 120f / 20
                val segmentY = segment * segmentHeight
                val segmentColor = when {
                    segment < 12 -> Color.Green
                    segment < 16 -> Color.Yellow
                    else -> Color.Red
                }
                
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(segmentHeight.dp)
                        .background(segmentColor.copy(alpha = 0.3f))
                        .offset(y = segmentY.dp)
                )
            }
            
            // Active level
            val activeSegments = (value * 20).toInt().coerceIn(0, 20)
            repeat(activeSegments) { segment ->
                val segmentHeight = 120f / 20
                val segmentY = (19 - segment) * segmentHeight
                val segmentColor = when {
                    segment < 8 -> Color.Green
                    segment < 12 -> Color.Yellow
                    else -> Color.Red
                }
                
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(segmentHeight.dp)
                        .background(segmentColor)
                        .offset(y = segmentY.dp)
                )
            }
        }
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Text(
            text = "${(value * 100).toInt()}%",
            style = MaterialTheme.typography.labelSmall,
            color = Color.White
        )
    }
}