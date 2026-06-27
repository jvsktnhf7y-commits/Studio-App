import React, { useState } from 'react';
import {
  View, Text, TextInput, StyleSheet, KeyboardAvoidingView,
  Platform, Alert, ScrollView, TouchableOpacity, StatusBar,
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
      Alert.alert('Connection error', 'Could not reach the server. Try again in 30 seconds.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      <LinearGradient colors={GRADIENT} style={styles.header} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <View style={styles.iconWrap}>
          <Text style={styles.icon}>🎵</Text>
        </View>
        <Text style={styles.headerTitle}>Teacher Sign In</Text>
        <Text style={styles.headerSub}>Studio App</Text>
      </LinearGradient>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
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

          <Button label="Sign In →" onPress={handleLogin} loading={loading} style={{ marginTop: 24 }} />

          <TouchableOpacity onPress={() => navigation.replace('RoleSelect')} style={styles.switchRole}>
            <Text style={styles.switchRoleText}>← Not a teacher? Switch role</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root:           { flex: 1, backgroundColor: COLORS.bg },
  header:         { paddingTop: 70, paddingBottom: 36, paddingHorizontal: 28, alignItems: 'flex-start' },
  iconWrap:       { width: 52, height: 52, borderRadius: 16, backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  icon:           { fontSize: 26 },
  headerTitle:    { fontSize: 28, fontWeight: '800', color: '#fff', marginBottom: 4 },
  headerSub:      { fontSize: 14, color: 'rgba(255,255,255,0.65)' },
  body:           { padding: 24, paddingTop: 32 },
  label:          { fontSize: 13, fontWeight: '600', color: COLORS.subtext, marginBottom: 8, marginTop: 16 },
  input:          { height: 52, backgroundColor: '#fff', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 14, paddingHorizontal: 16, fontSize: 16, color: COLORS.text },
  switchRole:     { marginTop: 24, alignItems: 'center' },
  switchRoleText: { fontSize: 14, color: COLORS.primary, fontWeight: '600' },
});
