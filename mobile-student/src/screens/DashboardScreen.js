import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import Card from '../components/Card';
import { getDashboard } from '../services/api';
import { COLORS } from '../theme';

const STUDENT_GRADIENT = ['#48bb78', '#667eea'];

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

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color="#48bb78" /></View>;
  if (!data)   return null;

  const latest = data.notes?.[0] || null;
  const next   = data.upcoming?.[0] || null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 48 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor="#48bb78" />}>

      <View style={styles.greeting}>
        <Text style={styles.greetingEmoji}>👋</Text>
        <Text style={styles.greetingText}>Hi, {data.student_name}!</Text>
        <Text style={styles.greetingSubtext}>{data.upcoming.length} upcoming lesson{data.upcoming.length !== 1 ? 's' : ''}</Text>
      </View>

      {next && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Next Lesson</Text>
          <Card style={styles.nextCard}>
            <Text style={styles.nextDate}>{formatDate(next.start)}</Text>
            <Text style={styles.nextTime}>{formatTime(next.start)}</Text>
          </Card>
        </View>
      )}

      {latest && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Latest Note from Teacher</Text>
          <Card style={styles.noteCard}>
            <Text style={styles.noteDate}>{formatDate(latest.date)}</Text>
            {!!latest.notes && <Text style={styles.noteText}>{latest.notes}</Text>}
            {!!latest.assignment && (
              <View style={styles.assignmentBox}>
                <Text style={styles.assignmentLabel}>📌 Your assignment</Text>
                <Text style={styles.assignmentText}>{latest.assignment}</Text>
              </View>
            )}
          </Card>
        </View>
      )}

      {data.upcoming.length > 1 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upcoming Lessons</Text>
          {data.upcoming.slice(1, 6).map((l, i) => (
            <Card key={i} style={styles.upcomingRow}>
              <Text style={styles.upcomingDate}>{formatDate(l.start)}</Text>
              <Text style={styles.upcomingTime}>{formatTime(l.start)}</Text>
            </Card>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.bg },
  center:          { flex: 1, justifyContent: 'center', alignItems: 'center' },
  greeting:        { alignItems: 'center', paddingVertical: 24, marginBottom: 8 },
  greetingEmoji:   { fontSize: 48, marginBottom: 8 },
  greetingText:    { fontSize: 28, fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  greetingSubtext: { fontSize: 15, color: COLORS.subtext },
  section:         { marginBottom: 20 },
  sectionTitle:    { fontSize: 13, fontWeight: '700', color: '#48bb78', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  nextCard:        { padding: 20, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  nextDate:        { fontSize: 18, fontWeight: '800', color: COLORS.text },
  nextTime:        { fontSize: 16, color: COLORS.subtext },
  noteCard:        { padding: 16 },
  noteDate:        { fontSize: 12, fontWeight: '700', color: '#48bb78', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  noteText:        { fontSize: 15, color: COLORS.text, lineHeight: 22, marginBottom: 10 },
  assignmentBox:   { backgroundColor: '#f0fff4', borderRadius: 10, padding: 12 },
  assignmentLabel: { fontSize: 12, fontWeight: '700', color: '#48bb78', marginBottom: 6 },
  assignmentText:  { fontSize: 15, color: COLORS.text, lineHeight: 22, fontWeight: '600' },
  upcomingRow:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 12, marginBottom: 6 },
  upcomingDate:    { fontSize: 14, fontWeight: '600', color: COLORS.text },
  upcomingTime:    { fontSize: 14, color: COLORS.subtext },
});
