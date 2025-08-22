package com.audioplayerpro.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.audioplayerpro.ui.theme.*

@Composable
fun ProStatusCard(
    isProUser: Boolean,
    onUpgradeClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .background(
                brush = if (isProUser) {
                    Brush.verticalGradient(
                        colors = listOf(
                            ProGradientStart,
                            ProGradientEnd
                        )
                    )
                } else {
                    Brush.verticalGradient(
                        colors = listOf(
                            MaterialTheme.colorScheme.surfaceVariant,
                            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f)
                        )
                    )
                },
                shape = RoundedCornerShape(16.dp)
            ),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(20.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Status icon
            Icon(
                imageVector = if (isProUser) Icons.Default.Star else Icons.Default.Lock,
                contentDescription = if (isProUser) "Pro User" else "Free User",
                tint = if (isProUser) ProAccent else MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.size(32.dp)
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Status text
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = if (isProUser) "Pro User" else "Free User",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = if (isProUser) ProAccent else MaterialTheme.colorScheme.onSurface
                )
                
                Text(
                    text = if (isProUser) {
                        "You have access to all premium features"
                    } else {
                        "Upgrade to unlock advanced features"
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isProUser) {
                        ProAccent.copy(alpha = 0.8f)
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    }
                )
            }
            
            // Action button
            if (!isProUser) {
                Button(
                    onClick = onUpgradeClick,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ProAccent
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "Upgrade",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
fun ProFeatureList(
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "Pro Features",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            ProFeatureItem(
                icon = Icons.Default.Equalizer,
                title = "Parametric Equalizer",
                description = "Advanced EQ with precise frequency control"
            )
            
            ProFeatureItem(
                icon = Icons.Default.AudioFile,
                title = "Stem Separation",
                description = "AI-powered audio separation into individual tracks"
            )
            
            ProFeatureItem(
                icon = Icons.Default.Tune,
                title = "Advanced DSP Effects",
                description = "Reverb, delay, chorus, and stereo widener"
            )
            
            ProFeatureItem(
                icon = Icons.Default.Download,
                title = "Audio Export",
                description = "Export processed audio in WAV/FLAC formats"
            )
            
            ProFeatureItem(
                icon = Icons.Default.Settings,
                title = "Unlimited Presets",
                description = "Save and manage unlimited EQ presets"
            )
        }
    }
}

@Composable
private fun ProFeatureItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    description: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = title,
            tint = ProAccent,
            modifier = Modifier.size(24.dp)
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
            )
        }
    }
}