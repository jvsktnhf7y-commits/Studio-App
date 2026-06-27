import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, GRADIENT } from '../theme';

const ROLES = [
  { id: 'teacher', emoji: '🎵', label: 'Teacher',  sub: 'Manage your studio' },
  { id: 'parent',  emoji: '👨‍👩‍👧', label: 'Parent',   sub: 'Track lessons & pay' },
  { id: 'student', emoji: '🎸', label: 'Student',  sub: 'View notes & schedule' },
];

export default function RoleSelectScreen({ navigation }) {
  async function pick(role) {
    await AsyncStorage.setItem('app_role', role);
    navigation.replace('Login', { role });
  }

  return (
    <LinearGradient colors={GRADIENT} style={styles.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
      <SafeAreaView style={styles.safe}>
        <View style={styles.hero}>
          <Text style={styles.logo}>🎼</Text>
          <Text style={styles.title}>Maestro</Text>
          <Text style={styles.sub}>Music Studio Manager</Text>
        </View>

        <View style={styles.cards}>
          <Text style={styles.prompt}>I am a…</Text>
          {ROLES.map(r => (
            <TouchableOpacity key={r.id} style={styles.card} onPress={() => pick(r.id)} activeOpacity={0.82}>
              <Text style={styles.cardEmoji}>{r.emoji}</Text>
              <View style={styles.cardText}>
                <Text style={styles.cardLabel}>{r.label}</Text>
                <Text style={styles.cardSub}>{r.sub}</Text>
              </View>
              <Text style={styles.arrow}>›</Text>
            </TouchableOpacity>
          ))}
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  safe:     { flex: 1, justifyContent: 'center', padding: 28 },
  hero:     { alignItems: 'center', marginBottom: 40 },
  logo:     { fontSize: 64, marginBottom: 10 },
  title:    { fontSize: 36, fontWeight: '800', color: '#fff', letterSpacing: -1 },
  sub:      { fontSize: 15, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  prompt:   { fontSize: 13, fontWeight: '700', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 14 },
  cards:    {},
  card:     { backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 18, padding: 20, marginBottom: 12, flexDirection: 'row', alignItems: 'center' },
  cardEmoji:{ fontSize: 32, marginRight: 16 },
  cardText: { flex: 1 },
  cardLabel:{ fontSize: 20, fontWeight: '800', color: '#fff', marginBottom: 2 },
  cardSub:  { fontSize: 13, color: 'rgba(255,255,255,0.65)' },
  arrow:    { fontSize: 30, color: 'rgba(255,255,255,0.5)', fontWeight: '300' },
});
