import React, { useState } from 'react';
import {
  View, Text, TextInput, StyleSheet,
  KeyboardAvoidingView, Platform, Alert, ScrollView, TouchableOpacity,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../components/Button';
import { login, registerPushToken } from '../services/api';
import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, GRADIENT } from '../theme';

export default function LoginScreen({ navigation }) {
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [loading,  setLoading]  = useState(false);

  async function handleLogin() {
    if (!email.trim() || !password) {
      Alert.alert('Missing fields', 'Please enter your email and password.');
      return;
    }
    setLoading(true);
    try {
      const res = await login(email.trim().toLowerCase(), password);
      if (res.ok) {
        await AsyncStorage.setItem('teacher_email', email.trim().toLowerCase());
        try {
          const { status } = await Notifications.requestPermissionsAsync();
          if (status === 'granted') {
            const token = (await Notifications.getExpoPushTokenAsync()).data;
            await registerPushToken(token);
          }
        } catch {}
        navigation.replace('Main');
      } else {
        Alert.alert('Login failed', res.error || 'Invalid credentials.');
      }
    } catch {
      Alert.alert('Connection error', 'Could not reach the server. The server may be waking up — please wait 30 seconds and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <LinearGradient colors={GRADIENT} style={styles.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

          <View style={styles.hero}>
            <Text style={styles.logo}>🎵</Text>
            <Text style={styles.appName}>Studio Manager</Text>
            <Text style={styles.tagline}>Your studio. Your schedule.</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Welcome back</Text>
            <Text style={styles.cardSub}>Sign in to your teacher account</Text>

            <Text style={styles.label}>Email address</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              placeholderTextColor={COLORS.muted}
              autoCapitalize="none"
              keyboardType="email-address"
              returnKeyType="next"
            />

            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              placeholderTextColor={COLORS.muted}
              secureTextEntry
              returnKeyType="done"
              onSubmitEditing={handleLogin}
            />

            <Button
              label="Sign In →"
              onPress={handleLogin}
              loading={loading}
              style={{ marginTop: 20 }}
            />
          </View>

        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  scroll:   { flexGrow: 1, justifyContent: 'center', padding: 24 },
  hero:     { alignItems: 'center', marginBottom: 32 },
  logo:     { fontSize: 60, marginBottom: 10 },
  appName:  { fontSize: 30, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  tagline:  { fontSize: 15, color: 'rgba(255,255,255,0.72)', marginTop: 4 },
  card:     {
    backgroundColor: '#fff',
    borderRadius: 24,
    padding: 28,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.18,
    shadowRadius: 20,
    elevation: 10,
  },
  cardTitle: { fontSize: 22, fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  cardSub:   { fontSize: 14, color: COLORS.subtext, marginBottom: 24 },
  label:     { fontSize: 13, fontWeight: '600', color: COLORS.subtext, marginBottom: 6, marginTop: 14 },
  input:     {
    height: 50,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    color: COLORS.text,
    backgroundColor: '#f8f9fe',
  },
});
