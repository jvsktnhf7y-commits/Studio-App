import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, GRADIENT, SHADOW } from '../theme';

export default function Button({ label, onPress, variant = 'primary', loading = false, disabled = false, style }) {
  const isDisabled = disabled || loading;

  if (variant === 'primary') {
    return (
      <TouchableOpacity
        onPress={onPress}
        disabled={isDisabled}
        activeOpacity={0.85}
        style={[{ borderRadius: 14, overflow: 'hidden', opacity: isDisabled ? 0.5 : 1 }, SHADOW, style]}
      >
        <LinearGradient colors={GRADIENT} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.inner}>
          {loading
            ? <ActivityIndicator color="#fff" size="small" />
            : <Text style={styles.primaryLabel}>{label}</Text>}
        </LinearGradient>
      </TouchableOpacity>
    );
  }

  const MAP = {
    success:   { bg: COLORS.success,  text: '#fff',         border: COLORS.success },
    danger:    { bg: COLORS.danger,   text: '#fff',         border: COLORS.danger },
    secondary: { bg: COLORS.bg,       text: COLORS.subtext, border: COLORS.border },
    outline:   { bg: 'transparent',   text: COLORS.primary, border: COLORS.primary },
  };
  const v = MAP[variant] || MAP.secondary;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.75}
      style={[styles.inner, { backgroundColor: v.bg, borderColor: v.border, borderWidth: 1.5, borderRadius: 14, opacity: isDisabled ? 0.5 : 1 }, style]}
    >
      {loading
        ? <ActivityIndicator color={v.text} size="small" />
        : <Text style={[styles.label, { color: v.text }]}>{label}</Text>}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  inner:        { height: 52, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 24 },
  primaryLabel: { color: '#fff', fontSize: 16, fontWeight: '700', letterSpacing: 0.2 },
  label:        { fontSize: 15, fontWeight: '600' },
});
