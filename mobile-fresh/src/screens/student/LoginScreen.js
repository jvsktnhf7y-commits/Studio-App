import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, KeyboardAvoidingView, Platform, Alert, ScrollView, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../../components/Button';
import { studentLogin } from '../../services/api';
import { COLORS } from '../../theme';

export default function StudentLoginScreen({ navigation }) {
  const [name,       setName]       = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [loading,    setLoading]    = useState(false);

  async function handleLogin() {
    if (!name.trim() || !accessCode.trim()) {
      Alert.alert('Missing fields', 'Please enter your name and access code.');
      return;
    }
    setLoading(true);
    try {
      const res = await studentLogin(name.trim(), accessCode.trim().toUpperCase());
      if (res.ok) {
        navigation.replace('Main');
      } else {
        Alert.alert('Login failed', res.error || 'Incorrect access code.');
      }
    } catch {
      Alert.alert('Connection error', 'Could not reach the server. Please try again in 30 seconds.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <LinearGradient colors={['#48bb78', '#38a169']} style={styles.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.hero}>
            <Text style={styles.logo}>🎸</Text>
            <Text style={styles.appName}>Maestro</Text>
            <Text style={styles.tagline}>Student Portal</Text>
          </View>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Welcome!</Text>
            <Text style={styles.cardSub}>Enter your name and the access code from your teacher</Text>

            <Text style={styles.label}>Your name</Text>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="First Last"
              placeholderTextColor={COLORS.muted}
              autoCapitalize="words"
              returnKeyType="next"
            />

            <Text style={styles.label}>Access code</Text>
            <TextInput
              style={styles.input}
              value={accessCode}
              onChangeText={setAccessCode}
              placeholder="e.g. MUSIC123"
              placeholderTextColor={COLORS.muted}
              autoCapitalize="characters"
              returnKeyType="done"
              onSubmitEditing={handleLogin}
            />

            <Button label="Sign In →" onPress={handleLogin} loading={loading} style={{ marginTop: 20 }} />

            <TouchableOpacity onPress={() => navigation.replace('RoleSelect')} style={styles.switchRole}>
              <Text style={styles.switchRoleText}>Not a student? Switch role</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient:       { flex: 1 },
  scroll:         { flexGrow: 1, justifyContent: 'center', padding: 24 },
  hero:           { alignItems: 'center', marginBottom: 32 },
  logo:           { fontSize: 60, marginBottom: 10 },
  appName:        { fontSize: 30, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  tagline:        { fontSize: 15, color: 'rgba(255,255,255,0.72)', marginTop: 4 },
  card:           { backgroundColor: '#fff', borderRadius: 24, padding: 28, shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.18, shadowRadius: 20, elevation: 10 },
  cardTitle:      { fontSize: 22, fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  cardSub:        { fontSize: 14, color: COLORS.subtext, marginBottom: 24, lineHeight: 20 },
  label:          { fontSize: 13, fontWeight: '600', color: COLORS.subtext, marginBottom: 6, marginTop: 14 },
  input:          { height: 50, borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12, paddingHorizontal: 16, fontSize: 16, color: COLORS.text, backgroundColor: '#f8f9fe' },
  switchRole:     { marginTop: 20, alignItems: 'center' },
  switchRoleText: { fontSize: 13, color: '#48bb78', fontWeight: '600' },
});
