package com.audioplayerpro.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlin.math.*

@Composable
fun EqualizerSlider(
    frequency: String,
    gain: Float,
    onGainChanged: (Float) -> Unit,
    modifier: Modifier = Modifier,
    minGain: Float = -12f,
    maxGain: Float = 12f
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Frequency label
        Text(
            text = frequency,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Medium
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Vertical slider
        Box(
            modifier = Modifier
                .width(40.dp)
                .height(120.dp),
            contentAlignment = Alignment.Center
        ) {
            // Slider track
            Canvas(
                modifier = Modifier
                    .fillMaxSize()
                    .pointerInput(Unit) {
                        detectDragGestures { _, dragAmount ->
                            val newGain = gain - (dragAmount.y / 10f)
                            onGainChanged(newGain.coerceIn(minGain, maxGain))
                        }
                    }
            ) {
                val canvasHeight = size.height
                val canvasWidth = size.width
                
                // Draw track background
                drawRect(
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
                    topLeft = Offset(canvasWidth / 2 - 2f, 0f),
                    size = Size(4f, canvasHeight)
                )
                
                // Draw track fill based on gain
                val normalizedGain = (gain - minGain) / (maxGain - minGain)
                val fillHeight = normalizedGain * canvasHeight
                val fillY = canvasHeight - fillHeight
                
                val trackColor = when {
                    gain > 0 -> MaterialTheme.colorScheme.primary
                    gain < 0 -> MaterialTheme.colorScheme.error
                    else -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                }
                
                drawRect(
                    color = trackColor,
                    topLeft = Offset(canvasWidth / 2 - 2f, fillY),
                    size = Size(4f, fillHeight)
                )
                
                // Draw center line
                drawRect(
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
                    topLeft = Offset(canvasWidth / 2 - 4f, canvasHeight / 2 - 1f),
                    size = Size(8f, 2f)
                )
                
                // Draw slider thumb
                val thumbY = canvasHeight - fillHeight
                drawCircle(
                    color = MaterialTheme.colorScheme.primary,
                    radius = 8f,
                    center = Offset(canvasWidth / 2, thumbY)
                )
                
                // Draw thumb border
                drawCircle(
                    color = MaterialTheme.colorScheme.onSurface,
                    radius = 8f,
                    center = Offset(canvasWidth / 2, thumbY),
                    style = Stroke(width = 2f)
                )
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Gain value display
        Text(
            text = "${if (gain >= 0) "+" else ""}${gain.toInt()}dB",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
    }
}

@Composable
fun ParametricBandSlider(
    frequency: Float,
    q: Float,
    gain: Float,
    onFrequencyChanged: (Float) -> Unit,
    onQChanged: (Float) -> Unit,
    onGainChanged: (Float) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // Frequency slider
            Text(
                text = "Frequency: ${frequency.toInt()} Hz",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Slider(
                value = frequency,
                onValueChange = onFrequencyChanged,
                valueRange = 20f..20000f,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Q (bandwidth) slider
            Text(
                text = "Q: ${String.format("%.1f", q)}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Slider(
                value = q,
                onValueChange = onQChanged,
                valueRange = 0.1f..10f,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Gain slider
            Text(
                text = "Gain: ${if (gain >= 0) "+" else ""}${gain.toInt()}dB",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Slider(
                value = gain,
                onValueChange = onGainChanged,
                valueRange = -12f..12f,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
fun DSPControlSlider(
    title: String,
    value: Float,
    onValueChanged: (Float) -> Unit,
    valueRange: ClosedFloatingPointRange<Float>,
    unit: String = "",
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = "${String.format("%.1f", value)}$unit",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
            )
        }
        
        Slider(
            value = value,
            onValueChange = onValueChanged,
            valueRange = valueRange,
            modifier = Modifier.fillMaxWidth()
        )
    }
}