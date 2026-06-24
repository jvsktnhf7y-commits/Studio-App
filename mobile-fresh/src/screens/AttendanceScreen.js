import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ActivityIndicator, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../components/Card';
import Button from '../components/Button';
import { recordAttendance } from '../services/api';
import { COLORS, GRADIENT, SHADOW } from '../theme';

const ACTIONS = [
  {
    status:  'confirmed',
    emoji:   '✅',
    label:   'Confirmed',
    desc:    'Student attended — lesson fee deducted',
    color:   COLORS.success,
    bg:      COLORS.successBg,
  },
  {
    status:  'missed',
    emoji:   '❌',
    label:   'Missed',
    desc:    'No-show — lesson fee still deducted',
    color:   COLORS.danger,
    bg:      COLORS.dangerBg,
  },
  {
    status:  'cancelled',
    emoji:   '🔄',
    label:   'Cancelled',
    desc:    'Cancelled in advance — no charge',
    color:   COLORS.muted,
    bg:      COLORS.bg,
  },
];

export default function AttendanceScreen({ route, navigation }) {
  const { lesson, date } = route.params;
  const [submitting, setSubmitting] = useState(false);
  const [result,     setResult]     = useState(null);

  async function submit(status) {
    setSubmitting(true);
    try {
      const res = await recordAttendance(
        lesson.student_name,
        status,
        date,
        lesson.duration_minutes || 60,
      );
      if (res.ok) {
        setResult({ status, charge: res.charge, new_balance: res.new_balance });
      } else {
        Alert.alert('Error', res.error || 'Failed to record attendance.');
      }
    } catch {
      Alert.alert('Error', 'Could not connect to server.');
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    const action = ACTIONS.find(a => a.status === result.status);
    return (
      <View style={styles.successContainer}>
        <LinearGradient colors={GRADIENT} style={styles.successBanner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
          <Text style={styles.successEmoji}>{action?.emoji}</Text>
          <Text style={styles.successTitle}>Recorded!</Text>
          <Text style={styles.successName}>{lesson.student_name}</Text>
        </LinearGradient>

        <View style={styles.successBody}>
          <Card style={styles.resultCard}>
            <View style={styles.resultRow}>
              <Text style={styles.resultLabel}>Status</Text>
              <Text style={[styles.resultValue, { color: action?.color }]}>{action?.label}</Text>
            </View>
            {result.charge > 0 && (
              <View style={styles.resultRow}>
                <Text style={styles.resultLabel}>Fee charged</Text>
                <Text style={[styles.resultValue, { color: COLORS.danger }]}>−${result.charge.toFixed(2)}</Text>
              </View>
            )}
            <View style={[styles.resultRow, { borderBottomWidth: 0 }]}>
              <Text style={styles.resultLabel}>New balance</Text>
              <Text style={[styles.resultValue, { color: result.new_balance < 0 ? COLORS.danger : COLORS.success }]}>
                ${result.new_balance.toFixed(2)}
              </Text>
            </View>
          </Card>

          <Button
            label="✏️  Add Lesson Note"
            onPress={() => navigation.navigate('LessonNote', { studentName: lesson.student_name, date })}
            style={{ marginTop: 8 }}
          />
          <Button
            label="← Back to Dashboard"
            onPress={() => navigation.navigate('Today')}
            variant="secondary"
            style={{ marginTop: 10 }}
          />
        </View>
      </View>
    );
  }

  const balance      = lesson.prepaid_balance ?? 0;
  const balanceColor = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;
  const balanceBg    = balance < 0 ? COLORS.dangerBg : balance < 50 ? COLORS.warningBg : COLORS.successBg;

  return (
    <View style={styles.container}>
      <Card style={styles.infoCard}>
        <Text style={styles.studentName}>{lesson.student_name}</Text>
        <Text style={styles.meta}>
          {lesson.duration_minutes || 60} min  ·  ${lesson.rate}/hr
        </Text>
        <View style={[styles.balancePill, { backgroundColor: balanceBg }]}>
          <Text style={[styles.balanceText, { color: balanceColor }]}>
            Balance: ${balance.toFixed(2)}
          </Text>
        </View>
      </Card>

      <Text style={styles.prompt}>What happened?</Text>

      {submitting ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        ACTIONS.map((action) => (
          <TouchableOpacity
            key={action.status}
            style={[styles.actionCard, { backgroundColor: action.bg, borderColor: action.color }, SHADOW]}
            onPress={() => submit(action.status)}
            activeOpacity={0.75}
          >
            <Text style={styles.actionEmoji}>{action.emoji}</Text>
            <View style={styles.actionInfo}>
              <Text style={[styles.actionLabel, { color: action.color }]}>{action.label}</Text>
              <Text style={styles.actionDesc}>{action.desc}</Text>
            </View>
            <Text style={[styles.actionArrow, { color: action.color }]}>›</Text>
          </TouchableOpacity>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container:        { flex: 1, backgroundColor: COLORS.bg, padding: 16 },
  infoCard:         { marginBottom: 8 },
  studentName:      { fontSize: 22, fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  meta:             { fontSize: 14, color: COLORS.subtext, marginBottom: 10 },
  balancePill:      { alignSelf: 'flex-start', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 4 },
  balanceText:      { fontSize: 14, fontWeight: '700' },
  prompt:           { fontSize: 15, fontWeight: '700', color: COLORS.subtext, marginTop: 8, marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.8 },
  actionCard:       { flexDirection: 'row', alignItems: 'center', borderRadius: 16, borderWidth: 1.5, padding: 16, marginBottom: 10 },
  actionEmoji:      { fontSize: 26, marginRight: 14 },
  actionInfo:       { flex: 1 },
  actionLabel:      { fontSize: 16, fontWeight: '800', marginBottom: 2 },
  actionDesc:       { fontSize: 13, color: COLORS.muted },
  actionArrow:      { fontSize: 28, fontWeight: '300', marginLeft: 8 },

  successContainer: { flex: 1, backgroundColor: COLORS.bg },
  successBanner:    { paddingTop: 50, paddingBottom: 40, alignItems: 'center' },
  successEmoji:     { fontSize: 56, marginBottom: 8 },
  successTitle:     { fontSize: 32, fontWeight: '800', color: '#fff', marginBottom: 4 },
  successName:      { fontSize: 18, color: 'rgba(255,255,255,0.8)' },
  successBody:      { flex: 1, padding: 20 },
  resultCard:       { marginBottom: 16 },
  resultRow:        { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  resultLabel:      { fontSize: 15, color: COLORS.subtext },
  resultValue:      { fontSize: 15, fontWeight: '700' },
});
