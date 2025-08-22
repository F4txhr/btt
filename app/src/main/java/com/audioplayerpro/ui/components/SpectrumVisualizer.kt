package com.audioplayerpro.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.unit.dp
import kotlin.math.*

@Composable
fun SpectrumVisualizer(
    spectrumData: FloatArray,
    modifier: Modifier = Modifier,
    barCount: Int = 64,
    barWidth: Float = 4f,
    barSpacing: Float = 2f,
    maxHeight: Float = 200f,
    smoothing: Float = 0.8f
) {
    var animatedSpectrum by remember { mutableStateOf(FloatArray(barCount) { 0f }) }
    
    // Animate spectrum data changes
    LaunchedEffect(spectrumData) {
        animatedSpectrum = animatedSpectrum.mapIndexed { index, current ->
            val target = if (index < spectrumData.size) spectrumData[index] else 0f
            animate(
                initialValue = current,
                targetValue = target,
                animationSpec = tween(
                    durationMillis = (100 * (1f - smoothing)).toInt(),
                    easing = FastOutSlowInEasing
                )
            ) { value, _ ->
                animatedSpectrum[index] = value
            }
        }.toFloatArray()
    }
    
    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(maxHeight.dp)
    ) {
        val canvasWidth = size.width
        val canvasHeight = size.height
        val totalBarWidth = barWidth + barSpacing
        val totalWidth = barCount * totalBarWidth
        val startX = (canvasWidth - totalWidth) / 2
        
        // Create gradient brush for bars
        val gradientBrush = Brush.verticalGradient(
            colors = listOf(
                MaterialTheme.colorScheme.primary,
                MaterialTheme.colorScheme.secondary,
                MaterialTheme.colorScheme.tertiary
            )
        )
        
        // Draw spectrum bars
        for (i in 0 until barCount) {
            val barHeight = animatedSpectrum[i] * canvasHeight
            val x = startX + i * totalBarWidth
            
            // Draw bar background
            drawRect(
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
                topLeft = Offset(x, canvasHeight - barHeight),
                size = Size(barWidth, barHeight)
            )
            
            // Draw gradient bar
            drawRect(
                brush = gradientBrush,
                topLeft = Offset(x, canvasHeight - barHeight),
                size = Size(barWidth, barHeight)
            )
            
            // Draw bar highlight
            drawRect(
                color = Color.White.copy(alpha = 0.3f),
                topLeft = Offset(x, canvasHeight - barHeight),
                size = Size(barWidth, min(barHeight, 4f))
            )
        }
    }
}

@Composable
fun WaveformVisualizer(
    waveformData: FloatArray,
    modifier: Modifier = Modifier,
    lineColor: Color = MaterialTheme.colorScheme.primary,
    backgroundColor: Color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
) {
    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(100.dp)
    ) {
        val canvasWidth = size.width
        val canvasHeight = size.height
        val centerY = canvasHeight / 2
        
        // Draw background
        drawRect(
            color = backgroundColor,
            size = size
        )
        
        // Draw waveform
        if (waveformData.isNotEmpty()) {
            val path = Path()
            val stepX = canvasWidth / (waveformData.size - 1)
            
            path.moveTo(0f, centerY)
            
            for (i in waveformData.indices) {
                val x = i * stepX
                val y = centerY + (waveformData[i] * centerY)
                path.lineTo(x, y)
            }
            
            drawPath(
                path = path,
                color = lineColor,
                style = Stroke(
                    width = 2f,
                    cap = StrokeCap.Round,
                    join = StrokeJoin.Round
                )
            )
        }
    }
}

@Composable
fun PeakMeter(
    leftPeak: Float,
    rightPeak: Float,
    rmsLevel: Float,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Left channel meter
        Column(
            modifier = Modifier.weight(1f),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "L",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            PeakMeterBar(
                peak = leftPeak,
                modifier = Modifier
                    .width(20.dp)
                    .height(100.dp)
            )
        }
        
        // RMS meter
        Column(
            modifier = Modifier.weight(1f),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "RMS",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            PeakMeterBar(
                peak = rmsLevel,
                modifier = Modifier
                    .width(20.dp)
                    .height(100.dp),
                color = MaterialTheme.colorScheme.secondary
            )
        }
        
        // Right channel meter
        Column(
            modifier = Modifier.weight(1f),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "R",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            PeakMeterBar(
                peak = rightPeak,
                modifier = Modifier
                    .width(20.dp)
                    .height(100.dp)
            )
        }
    }
}

@Composable
private fun PeakMeterBar(
    peak: Float,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.primary
) {
    Canvas(modifier = modifier) {
        val canvasHeight = size.height
        val canvasWidth = size.width
        val barHeight = peak * canvasHeight
        
        // Draw background
        drawRect(
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
            size = size
        )
        
        // Draw peak bar
        drawRect(
            color = color,
            topLeft = Offset(0f, canvasHeight - barHeight),
            size = Size(canvasWidth, barHeight)
        )
        
        // Draw peak indicator
        if (peak > 0.95f) {
            drawRect(
                color = Color.Red,
                topLeft = Offset(0f, 0f),
                size = Size(canvasWidth, 4f)
            )
        }
    }
}