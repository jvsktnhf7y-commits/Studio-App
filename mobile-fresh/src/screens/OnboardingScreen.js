import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, GRADIENT } from '../theme';

const { width } = Dimensions.get('window');

const SLIDES = [
  {
    emoji: '📅',
    title: "Today's Lessons",
    body: "See every student scheduled for today, pulled live from your Google Calendar. Tap any lesson to record attendance with one tap.",
  },
  {
    emoji: '🗓️',
    title: '14-Day Schedule',
    body: "See your full upcoming schedule at a glance. Tap the ✓ button on any lesson to record attendance in advance.",
  },
  {
    emoji: '👥',
    title: 'Student Profiles',
    body: "Tap any student to see their balance, attendance history, and lesson notes. Generate their Student app access code right from their profile.",
  },
  {
    emoji: '💳',
    title: 'Record Payments',
    body: "Log cash, Venmo, Zelle, or card payments on the spot. Balances update instantly across the web app and parent portal.",
  },
  {
    emoji: '✏️',
    title: 'Lesson Notes',
    body: "Write notes and assignments right after each lesson. Parents and students can see them in their own apps instantly.",
  },
];

export default function OnboardingScreen({ navigation }) {
  const [index, setIndex] = useState(0);
  const slide = SLIDES[index];
  const isLast = index === SLIDES.length - 1;

  async function finish() {
    await AsyncStorage.setItem('onboarding_done', '1');
    navigation.replace('Login');
  }

  return (
    <LinearGradient colors={GRADIENT} style={styles.container} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
      <TouchableOpacity style={styles.skipBtn} onPress={finish}>
        <Text style={styles.skipText}>Skip</Text>
      </TouchableOpacity>

      <View style={styles.content}>
        <Text style={styles.emoji}>{slide.emoji}</Text>
        <Text style={styles.title}>{slide.title}</Text>
        <Text style={styles.body}>{slide.body}</Text>
      </View>

      <View style={styles.dots}>
        {SLIDES.map((_, i) => (
          <View key={i} style={[styles.dot, i === index && styles.dotActive]} />
        ))}
      </View>

      <TouchableOpacity
        style={styles.nextBtn}
        onPress={isLast ? finish : () => setIndex(index + 1)}
        activeOpacity={0.85}
      >
        <View style={styles.nextBtnInner}>
          <Text style={styles.nextBtnText}>{isLast ? "Let's go →" : 'Next →'}</Text>
        </View>
      </TouchableOpacity>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container:   { flex: 1, paddingHorizontal: 32 },
  skipBtn:     { position: 'absolute', top: 56, right: 24 },
  skipText:    { color: 'rgba(255,255,255,0.65)', fontSize: 15, fontWeight: '600' },
  content:     { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emoji:       { fontSize: 80, marginBottom: 28 },
  title:       { fontSize: 28, fontWeight: '800', color: '#fff', textAlign: 'center', marginBottom: 16, letterSpacing: -0.5 },
  body:        { fontSize: 16, color: 'rgba(255,255,255,0.82)', textAlign: 'center', lineHeight: 24 },
  dots:        { flexDirection: 'row', justifyContent: 'center', gap: 8, marginBottom: 32 },
  dot:         { width: 8, height: 8, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.35)' },
  dotActive:   { backgroundColor: '#fff', width: 24 },
  nextBtn:     { marginBottom: 56 },
  nextBtnInner:{ backgroundColor: '#fff', borderRadius: 16, paddingVertical: 16, alignItems: 'center' },
  nextBtnText: { color: COLORS.primary, fontSize: 17, fontWeight: '800' },
});
