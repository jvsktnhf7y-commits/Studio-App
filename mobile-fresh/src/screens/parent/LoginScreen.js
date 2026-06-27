import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, KeyboardAvoidingView, Platform, Alert, ScrollView, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Button from '../../components/Button';
import { parentLogin } from '../../services/api';
import { COLORS, GRADIENT } from '../../theme';

export default function ParentLoginScreen({ navigation }) {
  const [studentName, setStudentName] = useState('');
  const [code,        setCode]        = useState('');
  const [loading,     setLoading]     = useState(false);

  async function handleLogin() {
    if (!studentName.trim() || !code.trim()) {
      Alert.alert('Missing fields', "Enter your child's name and the parent code from your teacher.");
      return;
    }
    setLoading(true);
    try {
      const res = await parentLogin(studentName.trim(), code.trim().toUpperCase());
      if (res.ok) {
        await AsyncStorage.setItem('parent_student', studentName.trim());
        navigation.replace('Main');
      } else {
        Alert.alert('Login failed', res.error || 'Incorrect parent code.');
      }
    } catch {
      Alert.alert('Connection error', 'Could not reach the server. Please try again in 30 seconds.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <LinearGradient colors={['#667eea', '#f093fb']} style={styles.gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.hero}>
            <Text style={styles.logo}>👨‍👩‍👧</Text>
            <Text style={styles.appName}>Maestro</Text>
            <Text style={styles.tagline}>Parent Portal</Text>
          </View>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Welcome, parent!</Text>
            <Text style={styles.cardSub}>Enter your child's name and the parent code your teacher shared with you</Text>

            <Text style={styles.label}>Child's name</Text>
            <TextInput
              style={styles.input}
              value={studentName}
              onChangeText={setStudentName}
              placeholder="First Last"
              placeholderTextColor={COLORS.muted}
              autoCapitalize="words"
              returnKeyType="next"
            />

            <Text style={styles.label}>Parent code</Text>
            <TextInput
              style={styles.input}
              value={code}
              onChangeText={setCode}
              placeholder="e.g. PARENT-A1B2"
              placeholderTextColor={COLORS.muted}
              autoCapitalize="characters"
              returnKeyType="done"
              onSubmitEditing={handleLogin}
            />

            <Button label="Sign In →" onPress={handleLogin} loading={loading} style={{ marginTop: 20 }} />

            <TouchableOpacity onPress={() => navigation.replace('RoleSelect')} style={styles.switchRole}>
              <Text style={styles.switchRoleText}>Not a parent? Switch role</Text>
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
  switchRoleText: { fontSize: 13, color: COLORS.primary, fontWeight: '600' },
});
