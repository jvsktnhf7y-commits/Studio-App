import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, KeyboardAvoidingView, Platform, Alert, ScrollView, TouchableOpacity, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../../components/Button';
import { studentLogin } from '../../services/api';
import { COLORS, GRADIENT_GREEN } from '../../theme';

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
      Alert.alert('Connection error', 'Could not reach the server. Try again in 30 seconds.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      <LinearGradient colors={GRADIENT_GREEN} style={styles.header} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <View style={styles.iconWrap}>
          <Text style={styles.icon}>🎸</Text>
        </View>
        <Text style={styles.headerTitle}>Student Sign In</Text>
        <Text style={styles.headerSub}>Studio App</Text>
      </LinearGradient>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
          <Text style={styles.label}>Your name</Text>
          <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="First Last" placeholderTextColor={COLORS.muted} autoCapitalize="words" returnKeyType="next" />

          <Text style={styles.label}>Access code</Text>
          <TextInput style={styles.input} value={accessCode} onChangeText={setAccessCode} placeholder="From your teacher" placeholderTextColor={COLORS.muted} autoCapitalize="characters" returnKeyType="done" onSubmitEditing={handleLogin} />

          <Text style={styles.hint}>Your teacher generates this code and shares it with you.</Text>

          <Button label="Sign In →" onPress={handleLogin} loading={loading} style={{ marginTop: 24 }} />

          <TouchableOpacity onPress={() => navigation.replace('RoleSelect')} style={styles.switchRole}>
            <Text style={styles.switchRoleText}>← Not a student? Switch role</Text>
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
  hint:           { fontSize: 13, color: COLORS.muted, marginTop: 10, lineHeight: 18 },
  switchRole:     { marginTop: 24, alignItems: 'center' },
  switchRoleText: { fontSize: 14, color: '#059669', fontWeight: '600' },
});
