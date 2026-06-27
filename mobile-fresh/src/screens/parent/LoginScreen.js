import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, KeyboardAvoidingView, Platform, Alert, ScrollView, TouchableOpacity, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Button from '../../components/Button';
import { parentLogin } from '../../services/api';
import { COLORS, GRADIENT_PARENT } from '../../theme';

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
      Alert.alert('Connection error', 'Could not reach the server. Try again in 30 seconds.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />
      <LinearGradient colors={GRADIENT_PARENT} style={styles.header} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <View style={styles.iconWrap}>
          <Text style={styles.icon}>👨‍👩‍👧</Text>
        </View>
        <Text style={styles.headerTitle}>Parent Sign In</Text>
        <Text style={styles.headerSub}>Studio App</Text>
      </LinearGradient>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
          <Text style={styles.label}>Your child's name</Text>
          <TextInput style={styles.input} value={studentName} onChangeText={setStudentName} placeholder="First Last" placeholderTextColor={COLORS.muted} autoCapitalize="words" returnKeyType="next" />

          <Text style={styles.label}>Parent code</Text>
          <TextInput style={styles.input} value={code} onChangeText={setCode} placeholder="From your teacher" placeholderTextColor={COLORS.muted} autoCapitalize="characters" returnKeyType="done" onSubmitEditing={handleLogin} />

          <Text style={styles.hint}>Your teacher generates this code from their app and sends it to you.</Text>

          <Button label="Sign In →" onPress={handleLogin} loading={loading} style={{ marginTop: 24 }} />

          <TouchableOpacity onPress={() => navigation.replace('RoleSelect')} style={styles.switchRole}>
            <Text style={styles.switchRoleText}>← Not a parent? Switch role</Text>
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
  switchRoleText: { fontSize: 14, color: COLORS.primary, fontWeight: '600' },
});
