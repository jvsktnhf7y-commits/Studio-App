import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../theme';

const ROLES = [
  {
    id:      'teacher',
    emoji:   '🎵',
    label:   'Teacher',
    sub:     'Manage your studio',
    accent:  '#4f46e5',
    light:   '#eef2ff',
  },
  {
    id:      'parent',
    emoji:   '👨‍👩‍👧',
    label:   'Parent',
    sub:     'Track lessons & payments',
    accent:  '#7c3aed',
    light:   '#f5f3ff',
  },
  {
    id:      'student',
    emoji:   '🎸',
    label:   'Student',
    sub:     'View notes & schedule',
    accent:  '#059669',
    light:   '#ecfdf5',
  },
];

export default function RoleSelectScreen({ navigation }) {
  async function pick(role) {
    await AsyncStorage.setItem('app_role', role);
    navigation.replace('Login', { role });
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      <View style={styles.top}>
        <View style={styles.logoWrap}>
          <Text style={styles.logoEmoji}>🎼</Text>
        </View>
        <Text style={styles.appName}>Studio App</Text>
        <Text style={styles.tagline}>Music studio management</Text>
      </View>

      <SafeAreaView style={styles.bottom}>
        <Text style={styles.prompt}>Who are you?</Text>

        {ROLES.map(r => (
          <TouchableOpacity key={r.id} style={styles.card} onPress={() => pick(r.id)} activeOpacity={0.88}>
            <View style={[styles.iconBox, { backgroundColor: r.light }]}>
              <Text style={styles.emoji}>{r.emoji}</Text>
            </View>
            <View style={styles.cardBody}>
              <Text style={styles.cardLabel}>{r.label}</Text>
              <Text style={styles.cardSub}>{r.sub}</Text>
            </View>
            <View style={[styles.arrow, { backgroundColor: r.light }]}>
              <Text style={[styles.arrowText, { color: r.accent }]}>›</Text>
            </View>
          </TouchableOpacity>
        ))}

        <Text style={styles.footer}>Codes provided by your teacher</Text>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root:      { flex: 1, backgroundColor: COLORS.dark },
  top:       { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 60, paddingBottom: 40 },
  logoWrap:  { width: 80, height: 80, borderRadius: 24, backgroundColor: 'rgba(255,255,255,0.08)', alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  logoEmoji: { fontSize: 40 },
  appName:   { fontSize: 34, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  tagline:   { fontSize: 15, color: 'rgba(255,255,255,0.45)', marginTop: 6 },

  bottom:    { backgroundColor: '#fff', borderTopLeftRadius: 32, borderTopRightRadius: 32, padding: 28, paddingTop: 24 },
  prompt:    { fontSize: 13, fontWeight: '700', color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 16 },

  card:      { flexDirection: 'row', alignItems: 'center', padding: 16, borderRadius: 18, borderWidth: 1.5, borderColor: COLORS.border, marginBottom: 12, backgroundColor: '#fff' },
  iconBox:   { width: 52, height: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  emoji:     { fontSize: 26 },
  cardBody:  { flex: 1 },
  cardLabel: { fontSize: 17, fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  cardSub:   { fontSize: 13, color: COLORS.muted },
  arrow:     { width: 34, height: 34, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  arrowText: { fontSize: 22, fontWeight: '600', lineHeight: 28 },

  footer:    { textAlign: 'center', fontSize: 12, color: COLORS.muted, marginTop: 8 },
});
