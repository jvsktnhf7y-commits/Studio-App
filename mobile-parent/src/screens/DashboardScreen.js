import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../components/Card';
import { getDashboard } from '../services/api';
import { COLORS, GRADIENT } from '../theme';

function formatDate(str) {
  if (!str) return '';
  try { return new Date(str.length === 10 ? str + 'T12:00:00' : str).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }); } catch { return str; }
}
function formatTime(str) {
  if (!str) return '';
  try { return new Date(str).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch { return ''; }
}

export default function DashboardScreen() {
  const [data,       setData]       = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const res = await getDashboard();
      if (res.ok) setData(res);
    } catch { Alert.alert('Error', 'Could not load dashboard.'); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  if (!data)   return null;

  const balance      = data.balance ?? 0;
  const balanceColor = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;
  const balanceBg    = balance < 0 ? COLORS.dangerBg : balance < 50 ? COLORS.warningBg : COLORS.successBg;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 48 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />}>

      <LinearGradient colors={GRADIENT} style={styles.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <Text style={styles.heroSub}>Lessons for</Text>
        <Text style={styles.heroName}>{data.student_name}</Text>
        <View style={[styles.balancePill, { backgroundColor: 'rgba(255,255,255,0.2)' }]}>
          <Text style={styles.balanceLabel}>Prepaid Balance</Text>
          <Text style={[styles.balanceValue, { color: balance < 0 ? '#fc8181' : '#68d391' }]}>${balance.toFixed(2)}</Text>
        </View>
      </LinearGradient>

      {data.latest_note && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Latest Lesson Note</Text>
          <Card style={styles.noteCard}>
            <Text style={styles.noteDate}>{formatDate(data.latest_note.date)}</Text>
            <Text style={styles.noteText}>{data.latest_note.notes}</Text>
            {!!data.latest_note.assignment && (
              <View style={styles.assignmentRow}>
                <Text style={styles.assignmentLabel}>📌 Assignment: </Text>
                <Text style={styles.assignmentText}>{data.latest_note.assignment}</Text>
              </View>
            )}
          </Card>
        </View>
      )}

      {data.upcoming.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upcoming Lessons</Text>
          {data.upcoming.slice(0, 5).map((l, i) => (
            <Card key={i} style={styles.lessonRow}>
              <Text style={styles.lessonDate}>{formatDate(l.start)}</Text>
              <Text style={styles.lessonTime}>{formatTime(l.start)}</Text>
            </Card>
          ))}
        </View>
      )}

      {data.ledger.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          {data.ledger.slice(0, 8).map((r, i) => {
            const isPayment = r.status === 'Payment';
            return (
              <View key={i} style={styles.ledgerRow}>
                <View style={[styles.dot, { backgroundColor: isPayment ? COLORS.success : r.status === 'confirmed' ? COLORS.primary : COLORS.muted }]} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.ledgerDate}>{formatDate(r.date)}</Text>
                  <Text style={styles.ledgerStatus}>{r.status}</Text>
                </View>
                <Text style={[styles.ledgerAmount, { color: isPayment ? COLORS.success : COLORS.danger }]}>
                  {isPayment ? '+' : '-'}${Math.abs(parseFloat(r.amount || 0)).toFixed(2)}
                </Text>
              </View>
            );
          })}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:      { flex: 1, backgroundColor: COLORS.bg },
  center:         { flex: 1, justifyContent: 'center', alignItems: 'center' },
  hero:           { borderRadius: 20, padding: 24, marginBottom: 20 },
  heroSub:        { fontSize: 13, color: 'rgba(255,255,255,0.7)', marginBottom: 2 },
  heroName:       { fontSize: 26, fontWeight: '800', color: '#fff', marginBottom: 16 },
  balancePill:    { borderRadius: 14, padding: 14 },
  balanceLabel:   { fontSize: 12, color: 'rgba(255,255,255,0.75)', marginBottom: 4 },
  balanceValue:   { fontSize: 28, fontWeight: '800' },
  section:        { marginBottom: 20 },
  sectionTitle:   { fontSize: 13, fontWeight: '700', color: COLORS.primary, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  noteCard:       { padding: 14 },
  noteDate:       { fontSize: 12, color: COLORS.primary, fontWeight: '600', marginBottom: 6 },
  noteText:       { fontSize: 14, color: COLORS.text, lineHeight: 20, marginBottom: 6 },
  assignmentRow:  { flexDirection: 'row', flexWrap: 'wrap', backgroundColor: COLORS.successBg, borderRadius: 8, padding: 10, marginTop: 4 },
  assignmentLabel:{ fontSize: 13, fontWeight: '700', color: COLORS.success },
  assignmentText: { fontSize: 13, color: COLORS.text, flex: 1 },
  lessonRow:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 12, marginBottom: 6 },
  lessonDate:     { fontSize: 14, fontWeight: '600', color: COLORS.text },
  lessonTime:     { fontSize: 14, color: COLORS.subtext },
  ledgerRow:      { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  dot:            { width: 8, height: 8, borderRadius: 4, marginRight: 12 },
  ledgerDate:     { fontSize: 12, color: COLORS.muted, marginBottom: 2 },
  ledgerStatus:   { fontSize: 14, fontWeight: '600', color: COLORS.text },
  ledgerAmount:   { fontSize: 14, fontWeight: '700', minWidth: 60, textAlign: 'right' },
});
