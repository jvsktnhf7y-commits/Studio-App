import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  RefreshControl, ActivityIndicator, Alert, TouchableOpacity,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../components/Card';
import { getStudentProfile } from '../services/api';
import { COLORS, GRADIENT, SHADOW_SM } from '../theme';

function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr.length === 10 ? dateStr + 'T12:00:00' : dateStr)
      .toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return dateStr; }
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  try {
    return new Date(isoStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

const STATUS_STYLES = {
  confirmed: { color: COLORS.success, bg: COLORS.successBg, label: 'Confirmed' },
  missed:    { color: COLORS.danger,  bg: COLORS.dangerBg,  label: 'Missed'    },
  cancelled: { color: COLORS.muted,   bg: COLORS.bg,        label: 'Cancelled' },
  Payment:   { color: COLORS.primary, bg: '#ede9fe',        label: 'Payment'   },
};

export default function StudentProfileScreen({ route, navigation }) {
  const { name } = route.params;
  const [data,       setData]       = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const res = await getStudentProfile(name);
      if (res.ok) setData(res);
      else Alert.alert('Error', res.error || 'Failed to load profile.');
    } catch {
      Alert.alert('Error', 'Could not connect to server.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [name]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    navigation.setOptions({
      title: name,
      headerRight: () => (
        <TouchableOpacity
          onPress={() => navigation.navigate('Payment', { studentName: name })}
          style={{ marginRight: 16 }}
        >
          <Text style={{ color: COLORS.primary, fontWeight: '700', fontSize: 15 }}>+ Payment</Text>
        </TouchableOpacity>
      ),
    });
  }, [navigation, name]);

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }
  if (!data) return null;

  const balance      = data.balance ?? 0;
  const balanceColor = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ padding: 16, paddingBottom: 48 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />}
    >
      {/* Header card */}
      <LinearGradient colors={GRADIENT} style={styles.heroCard} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <Text style={styles.heroName}>{data.name}</Text>
        <Text style={styles.heroTier}>{data.tier || 'No tier'} · ${data.rate}/hr</Text>
        <View style={styles.heroBalanceRow}>
          <Text style={styles.heroBalanceLabel}>Balance</Text>
          <Text style={[styles.heroBalance, { color: balance < 0 ? '#fc8181' : '#68d391' }]}>
            ${balance.toFixed(2)}
          </Text>
        </View>
      </LinearGradient>

      {/* Upcoming lessons */}
      {data.upcoming.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upcoming Lessons</Text>
          {data.upcoming.map((l, i) => (
            <Card key={i} style={styles.rowCard}>
              <Text style={styles.rowDate}>{formatDate(l.start)}</Text>
              <Text style={styles.rowTime}>{formatTime(l.start)}</Text>
            </Card>
          ))}
        </View>
      )}

      {/* Lesson notes */}
      {data.notes.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Lesson Notes</Text>
          {data.notes.map((n, i) => (
            <Card key={i} style={styles.noteCard}>
              <Text style={styles.noteDate}>{formatDate(n.date)}</Text>
              <Text style={styles.noteText}>{n.notes}</Text>
              {!!n.assignment && (
                <View style={styles.assignmentRow}>
                  <Text style={styles.assignmentLabel}>Assignment: </Text>
                  <Text style={styles.assignmentText}>{n.assignment}</Text>
                </View>
              )}
            </Card>
          ))}
        </View>
      )}

      {/* Attendance / payment history */}
      {data.attendance.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent History</Text>
          {data.attendance.map((a, i) => {
            const s = STATUS_STYLES[a.status] || { color: COLORS.muted, bg: COLORS.bg, label: a.status };
            const isPayment = a.status === 'Payment';
            return (
              <View key={i} style={styles.historyRow}>
                <View style={[styles.statusDot, { backgroundColor: s.color }]} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.historyDate}>{formatDate(a.date)}</Text>
                  <Text style={[styles.historyStatus, { color: s.color }]}>{s.label}</Text>
                </View>
                <Text style={[styles.historyAmount, { color: isPayment ? COLORS.success : COLORS.danger }]}>
                  {isPayment ? '+' : ''}{parseFloat(a.amount || 0).toFixed(2) !== '0.00' ? `$${Math.abs(parseFloat(a.amount || 0)).toFixed(2)}` : ''}
                </Text>
              </View>
            );
          })}
        </View>
      )}

      <TouchableOpacity
        style={styles.noteBtn}
        onPress={() => navigation.navigate('LessonNote', { studentName: name })}
        activeOpacity={0.8}
      >
        <LinearGradient colors={GRADIENT} style={styles.noteBtnGrad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
          <Text style={styles.noteBtnText}>✏️  Add Lesson Note</Text>
        </LinearGradient>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.bg },
  center:          { flex: 1, justifyContent: 'center', alignItems: 'center' },
  heroCard:        { borderRadius: 20, padding: 24, marginBottom: 20 },
  heroName:        { fontSize: 26, fontWeight: '800', color: '#fff', marginBottom: 4 },
  heroTier:        { fontSize: 14, color: 'rgba(255,255,255,0.75)', marginBottom: 16 },
  heroBalanceRow:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  heroBalanceLabel:{ fontSize: 14, color: 'rgba(255,255,255,0.75)' },
  heroBalance:     { fontSize: 28, fontWeight: '800' },
  section:         { marginBottom: 20 },
  sectionTitle:    { fontSize: 13, fontWeight: '700', color: COLORS.primary, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  rowCard:         { padding: 12, marginBottom: 6, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rowDate:         { fontSize: 14, fontWeight: '600', color: COLORS.text },
  rowTime:         { fontSize: 14, color: COLORS.subtext },
  noteCard:        { padding: 14, marginBottom: 8 },
  noteDate:        { fontSize: 12, fontWeight: '600', color: COLORS.primary, marginBottom: 4 },
  noteText:        { fontSize: 14, color: COLORS.text, lineHeight: 20 },
  assignmentRow:   { flexDirection: 'row', marginTop: 8, flexWrap: 'wrap' },
  assignmentLabel: { fontSize: 13, fontWeight: '700', color: COLORS.subtext },
  assignmentText:  { fontSize: 13, color: COLORS.text, flex: 1 },
  historyRow:      { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  statusDot:       { width: 8, height: 8, borderRadius: 4, marginRight: 12 },
  historyDate:     { fontSize: 12, color: COLORS.muted, marginBottom: 2 },
  historyStatus:   { fontSize: 14, fontWeight: '600' },
  historyAmount:   { fontSize: 14, fontWeight: '700', minWidth: 52, textAlign: 'right' },
  noteBtn:         { marginTop: 8, borderRadius: 14, overflow: 'hidden' },
  noteBtnGrad:     { paddingVertical: 14, alignItems: 'center' },
  noteBtnText:     { color: '#fff', fontSize: 16, fontWeight: '700' },
});
