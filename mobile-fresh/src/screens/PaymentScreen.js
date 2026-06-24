import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, StyleSheet,
  ScrollView, KeyboardAvoidingView, Platform, Alert, TouchableOpacity,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Button from '../components/Button';
import { recordPayment, getStudents } from '../services/api';
import { COLORS, GRADIENT } from '../theme';

const METHODS = ['Cash', 'Venmo', 'Zelle', 'Check', 'Card'];

export default function PaymentScreen({ route, navigation }) {
  const initialStudent = route.params?.studentName || '';
  const [student,   setStudent]   = useState(initialStudent);
  const [students,  setStudents]  = useState([]);
  const [amount,    setAmount]    = useState('');
  const [method,    setMethod]    = useState('Cash');
  const [notes,     setNotes]     = useState('');
  const [saving,    setSaving]    = useState(false);
  const [saved,     setSaved]     = useState(null);
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    getStudents().then(data => {
      if (data.ok) setStudents(data.students.map(s => s.name));
    }).catch(() => {});
  }, []);

  async function handleSave() {
    if (!student) { Alert.alert('Missing student', 'Please select a student.'); return; }
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) { Alert.alert('Invalid amount', 'Please enter a valid payment amount.'); return; }
    setSaving(true);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const res = await recordPayment(student, amt, method, notes.trim(), today);
      if (res.ok) {
        setSaved({ student, amount: amt, method, newBalance: res.new_balance });
      } else {
        Alert.alert('Error', res.error || 'Failed to record payment.');
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
          <Text style={styles.successEmoji}>💳</Text>
          <Text style={styles.successTitle}>Payment Recorded!</Text>
          <Text style={styles.successName}>{saved.student}</Text>
        </LinearGradient>
        <View style={styles.successBody}>
          <View style={styles.resultRow}>
            <Text style={styles.resultLabel}>Amount</Text>
            <Text style={[styles.resultValue, { color: COLORS.success }]}>+${saved.amount.toFixed(2)}</Text>
          </View>
          <View style={styles.resultRow}>
            <Text style={styles.resultLabel}>Method</Text>
            <Text style={styles.resultValue}>{saved.method}</Text>
          </View>
          <View style={[styles.resultRow, { borderBottomWidth: 0 }]}>
            <Text style={styles.resultLabel}>New Balance</Text>
            <Text style={[styles.resultValue, { color: saved.newBalance < 0 ? COLORS.danger : COLORS.success }]}>
              ${saved.newBalance.toFixed(2)}
            </Text>
          </View>
          <Button label="← Done" onPress={() => navigation.goBack()} style={{ marginTop: 24 }} />
        </View>
      </View>
    );
  }

  const filteredStudents = students.filter(s =>
    s.toLowerCase().includes(student.toLowerCase())
  );

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 48 }} keyboardShouldPersistTaps="handled">

        <Text style={styles.label}>Student</Text>
        <TextInput
          style={styles.input}
          value={student}
          onChangeText={t => { setStudent(t); setShowPicker(true); }}
          placeholder="Search student…"
          placeholderTextColor={COLORS.muted}
          onFocus={() => setShowPicker(true)}
        />
        {showPicker && student.length > 0 && filteredStudents.length > 0 && filteredStudents[0] !== student && (
          <View style={styles.dropdown}>
            {filteredStudents.slice(0, 5).map(s => (
              <TouchableOpacity key={s} onPress={() => { setStudent(s); setShowPicker(false); }} style={styles.dropdownItem}>
                <Text style={styles.dropdownText}>{s}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <Text style={styles.label}>Amount ($)</Text>
        <TextInput
          style={styles.input}
          value={amount}
          onChangeText={setAmount}
          placeholder="0.00"
          placeholderTextColor={COLORS.muted}
          keyboardType="decimal-pad"
        />

        <Text style={styles.label}>Payment Method</Text>
        <View style={styles.methodRow}>
          {METHODS.map(m => (
            <TouchableOpacity
              key={m}
              onPress={() => setMethod(m)}
              style={[styles.methodChip, method === m && styles.methodChipActive]}
            >
              <Text style={[styles.methodText, method === m && styles.methodTextActive]}>{m}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Notes (optional)</Text>
        <TextInput
          style={styles.input}
          value={notes}
          onChangeText={setNotes}
          placeholder="e.g. for June lessons"
          placeholderTextColor={COLORS.muted}
        />

        <Button
          label="Record Payment"
          onPress={handleSave}
          loading={saving}
          style={{ marginTop: 24 }}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container:          { flex: 1, backgroundColor: COLORS.bg },
  label:              { fontSize: 13, fontWeight: '600', color: COLORS.subtext, marginBottom: 6, marginTop: 16 },
  input:              { backgroundColor: '#fff', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12, paddingHorizontal: 14, height: 50, fontSize: 15, color: COLORS.text },
  dropdown:           { backgroundColor: '#fff', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12, marginTop: 4, overflow: 'hidden' },
  dropdownItem:       { padding: 14, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  dropdownText:       { fontSize: 15, color: COLORS.text },
  methodRow:          { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  methodChip:         { borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8, backgroundColor: '#fff' },
  methodChipActive:   { borderColor: COLORS.primary, backgroundColor: '#ede9fe' },
  methodText:         { fontSize: 14, color: COLORS.muted, fontWeight: '600' },
  methodTextActive:   { color: COLORS.primary },
  successContainer:   { flex: 1, backgroundColor: COLORS.bg },
  successBanner:      { paddingTop: 60, paddingBottom: 40, alignItems: 'center' },
  successEmoji:       { fontSize: 56, marginBottom: 8 },
  successTitle:       { fontSize: 32, fontWeight: '800', color: '#fff', marginBottom: 4 },
  successName:        { fontSize: 18, color: 'rgba(255,255,255,0.8)' },
  successBody:        { padding: 24 },
  resultRow:          { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  resultLabel:        { fontSize: 15, color: COLORS.subtext },
  resultValue:        { fontSize: 15, fontWeight: '700', color: COLORS.text },
});
