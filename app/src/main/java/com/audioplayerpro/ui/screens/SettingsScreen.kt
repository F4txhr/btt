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
fun SettingsScreen(
    viewModel: MainViewModel,
    onNavigateBack: () -> Unit
) {
    val isProUser by viewModel.isProUser.collectAsState()
    val isHighResEnabled by viewModel.isHighResEnabled.collectAsState()
    val isHighResSupported by viewModel.isHighResSupported.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
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
            // Pro Status
            ProStatusCard(isProUser)
            
            // Audio Settings
            AudioSettingsSection(
                isHighResEnabled = isHighResEnabled,
                isHighResSupported = isHighResSupported,
                onHighResToggle = { viewModel.enableHighRes(it) }
            )
            
            // App Settings
            AppSettingsSection()
            
            // About
            AboutSection()
        }
    }
}

@Composable
fun ProStatusCard(isProUser: Boolean) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isProUser) AudioPrimary else AudioSurface
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                if (isProUser) Icons.Default.Star else Icons.Default.StarBorder,
                contentDescription = "Pro Status",
                tint = Color.White,
                modifier = Modifier.size(48.dp)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = if (isProUser) "Pro User" else "Free User",
                style = MaterialTheme.typography.headlineSmall,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = if (isProUser) 
                    "You have access to all Pro features" 
                else 
                    "Upgrade to unlock Pro features",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.8f),
                textAlign = TextAlign.Center
            )
            
            if (!isProUser) {
                Spacer(modifier = Modifier.height(16.dp))
                
                Button(
                    onClick = { /* Navigate to Pro purchase */ },
                    colors = ButtonDefaults.buttonColors(containerColor = Color.White)
                ) {
                    Icon(Icons.Default.Star, contentDescription = "Upgrade to Pro")
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Upgrade to Pro", color = AudioPrimary)
                }
            }
        }
    }
}

@Composable
fun AudioSettingsSection(
    isHighResEnabled: Boolean,
    isHighResSupported: Boolean,
    onHighResToggle: (Boolean) -> Unit
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
                text = "Audio Settings",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // High-Resolution Audio
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "High-Resolution Audio",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White
                    )
                    Text(
                        text = "192 kHz, 32-bit float output",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.7f)
                    )
                }
                
                Switch(
                    checked = isHighResEnabled,
                    onCheckedChange = onHighResToggle,
                    enabled = isHighResSupported,
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = AudioPrimary,
                        checkedTrackColor = AudioPrimary.copy(alpha = 0.5f),
                        uncheckedThumbColor = Color.Gray,
                        uncheckedTrackColor = Color.Gray.copy(alpha = 0.5f)
                    )
                )
            }
            
            if (!isHighResSupported) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "High-resolution audio not supported on this device",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.Red.copy(alpha = 0.8f)
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Audio Format Support
            Text(
                text = "Supported Formats",
                style = MaterialTheme.typography.labelLarge,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            val formats = listOf("FLAC", "WAV", "MP3", "AAC", "OGG", "DSD")
            formats.chunked(3).forEach { row ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    row.forEach { format ->
                        Chip(
                            onClick = { },
                            colors = ChipDefaults.chipColors(
                                containerColor = AudioPrimary.copy(alpha = 0.2f)
                            )
                        ) {
                            Text(
                                text = format,
                                color = Color.White,
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
fun AppSettingsSection() {
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
                text = "App Settings",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Theme
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.Palette,
                    contentDescription = "Theme",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                Text(
                    text = "Theme",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White,
                    modifier = Modifier.weight(1f)
                )
                
                Text(
                    text = "Dark",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.7f)
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Auto-play
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.PlayArrow,
                    contentDescription = "Auto-play",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                Text(
                    text = "Auto-play next track",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White,
                    modifier = Modifier.weight(1f)
                )
                
                Switch(
                    checked = true,
                    onCheckedChange = { },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = AudioPrimary,
                        checkedTrackColor = AudioPrimary.copy(alpha = 0.5f),
                        uncheckedThumbColor = Color.Gray,
                        uncheckedTrackColor = Color.Gray.copy(alpha = 0.5f)
                    )
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Crossfade
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.Tune,
                    contentDescription = "Crossfade",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
                
                Spacer(modifier = Modifier.width(16.dp))
                
                Text(
                    text = "Crossfade between tracks",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White,
                    modifier = Modifier.weight(1f)
                )
                
                Switch(
                    checked = false,
                    onCheckedChange = { },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = AudioPrimary,
                        checkedTrackColor = AudioPrimary.copy(alpha = 0.5f),
                        uncheckedThumbColor = Color.Gray,
                        uncheckedTrackColor = Color.Gray.copy(alpha = 0.5f)
                    )
                )
            }
        }
    }
}

@Composable
fun AboutSection() {
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
                text = "About",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            AboutItem(
                icon = Icons.Default.Info,
                title = "Version",
                subtitle = "1.0.0"
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            AboutItem(
                icon = Icons.Default.Code,
                title = "Build",
                subtitle = "2024.01.01"
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            AboutItem(
                icon = Icons.Default.DeveloperMode,
                title = "Developer",
                subtitle = "Audio Player Pro Team"
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Button(
                onClick = { /* Open privacy policy */ },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent)
            ) {
                Text("Privacy Policy", color = AudioPrimary)
            }
            
            Button(
                onClick = { /* Open terms of service */ },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent)
            ) {
                Text("Terms of Service", color = AudioPrimary)
            }
        }
    }
}

@Composable
fun AboutItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            icon,
            contentDescription = title,
            tint = Color.White.copy(alpha = 0.7f),
            modifier = Modifier.size(20.dp)
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Text(
            text = title,
            style = MaterialTheme.typography.bodyMedium,
            color = Color.White,
            modifier = Modifier.weight(1f)
        )
        
        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodySmall,
            color = Color.White.copy(alpha = 0.7f)
        )
    }
}