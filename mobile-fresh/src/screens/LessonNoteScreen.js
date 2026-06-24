import React, { useState } from 'react';
import {
  View, Text, TextInput, StyleSheet,
  ScrollView, KeyboardAvoidingView, Platform, Alert, TouchableOpacity,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../components/Button';
import { saveLessonNote } from '../services/api';
import { COLORS, GRADIENT } from '../theme';

export default function LessonNoteScreen({ route, navigation }) {
  const { studentName, date: initialDate } = route.params;
  const today = new Date().toISOString().slice(0, 10);

  const [notes,      setNotes]      = useState('');
  const [assignment, setAssignment] = useState('');
  const [date,       setDate]       = useState(initialDate || today);
  const [saving,     setSaving]     = useState(false);
  const [saved,      setSaved]      = useState(false);

  async function handleSave() {
    if (!notes.trim()) {
      Alert.alert('Missing notes', 'Please write something in the lesson notes.');
      return;
    }
    setSaving(true);
    try {
      const res = await saveLessonNote(studentName, date, notes.trim(), assignment.trim());
      if (res.ok) {
        setSaved(true);
      } else {
        Alert.alert('Error', res.error || 'Failed to save note.');
      }
    } catch {
      Alert.alert('Error', 'Could not connect to server.');
    } finally {
      setSaving(false);
    }
  }

  if (saved) {
    return (
      <View style={styles.successContainer}>
        <LinearGradient colors={GRADIENT} style={styles.successBanner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
          <Text style={styles.successEmoji}>✏️</Text>
          <Text style={styles.successTitle}>Note Saved!</Text>
          <Text style={styles.successName}>{studentName}</Text>
        </LinearGradient>
        <View style={styles.successBody}>
          <Button label="← Back to Dashboard" onPress={() => navigation.navigate('Today')} />
          <TouchableOpacity onPress={() => { setNotes(''); setAssignment(''); setSaved(false); }} style={styles.anotherLink}>
            <Text style={styles.anotherText}>Add another note</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={{ padding: 16, paddingBottom: 48 }}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.studentChip}>
          <LinearGradient colors={GRADIENT} style={styles.chipGrad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
            <Text style={styles.chipText}>{studentName}</Text>
          </LinearGradient>
        </View>

        <Text style={styles.label}>Date</Text>
        <TextInput
          style={styles.input}
          value={date}
          onChangeText={setDate}
          placeholder="YYYY-MM-DD"
          placeholderTextColor={COLORS.muted}
        />

        <Text style={styles.label}>Lesson Notes</Text>
        <TextInput
          style={[styles.input, styles.multiline]}
          value={notes}
          onChangeText={setNotes}
          placeholder="What did you work on today?"
          placeholderTextColor={COLORS.muted}
          multiline
          numberOfLines={5}
          textAlignVertical="top"
        />

        <Text style={styles.label}>Assignment (optional)</Text>
        <TextInput
          style={[styles.input, styles.multiline]}
          value={assignment}
          onChangeText={setAssignment}
          placeholder="Practice this before next lesson…"
          placeholderTextColor={COLORS.muted}
          multiline
          numberOfLines={3}
          textAlignVertical="top"
        />

        <Button
          label="Save Note"
          onPress={handleSave}
          loading={saving}
          style={{ marginTop: 24 }}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container:        { flex: 1, backgroundColor: COLORS.bg },
  studentChip:      { alignSelf: 'flex-start', marginBottom: 20, borderRadius: 20, overflow: 'hidden' },
  chipGrad:         { paddingHorizontal: 14, paddingVertical: 6 },
  chipText:         { color: '#fff', fontWeight: '700', fontSize: 14 },
  label:            { fontSize: 13, fontWeight: '600', color: COLORS.subtext, marginBottom: 6, marginTop: 16 },
  input:            { backgroundColor: '#fff', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: COLORS.text },
  multiline:        { minHeight: 100, paddingTop: 12 },
  successContainer: { flex: 1, backgroundColor: COLORS.bg },
  successBanner:    { paddingTop: 60, paddingBottom: 40, alignItems: 'center' },
  successEmoji:     { fontSize: 56, marginBottom: 8 },
  successTitle:     { fontSize: 32, fontWeight: '800', color: '#fff', marginBottom: 4 },
  successName:      { fontSize: 18, color: 'rgba(255,255,255,0.8)' },
  successBody:      { padding: 20 },
  anotherLink:      { marginTop: 16, alignItems: 'center' },
  anotherText:      { color: COLORS.primary, fontWeight: '600', fontSize: 15 },
});
