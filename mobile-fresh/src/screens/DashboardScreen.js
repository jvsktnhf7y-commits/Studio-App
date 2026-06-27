import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl,
  ActivityIndicator, TouchableOpacity, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { getTodayLessons } from '../services/api';
import { COLORS, GRADIENT, SHADOW_CARD } from '../theme';

function formatTime(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch { return ''; }
}

function StatusPill({ status }) {
  const map = {
    confirmed: { bg: '#dcfce7', color: '#15803d', label: 'Confirmed' },
    missed:    { bg: '#fee2e2', color: '#dc2626', label: 'Missed' },
    cancelled: { bg: '#f4f4f5', color: '#71717a', label: 'Cancelled' },
  };
  const s = map[status] || { bg: '#f4f4f5', color: '#71717a', label: status };
  return (
    <View style={[styles.pill, { backgroundColor: s.bg }]}>
      <Text style={[styles.pillText, { color: s.color }]}>{s.label}</Text>
    </View>
  );
}

export default function DashboardScreen({ navigation }) {
  const [lessons,    setLessons]    = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const data = await getTodayLessons();
      if (data.ok) setLessons(data.lessons || []);
    } catch {
      Alert.alert('Error', 'Could not load lessons.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const now      = new Date();
  const upcoming = lessons.filter(l => !l.status && new Date(l.start) > now);
  const done     = lessons.filter(l => l.status);
  const next     = upcoming[0] || null;
  const todayStr = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
  const greeting = now.getHours() < 12 ? 'Good morning' : now.getHours() < 17 ? 'Good afternoon' : 'Good evening';

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: 40 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />}
    >
      <LinearGradient colors={GRADIENT} style={styles.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
        <Text style={styles.heroDate}>{todayStr}</Text>
        <Text style={styles.heroTitle}>{greeting} 👋</Text>
        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{lessons.length}</Text>
            <Text style={styles.statLbl}>Total today</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{upcoming.length}</Text>
            <Text style={styles.statLbl}>Remaining</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{done.length}</Text>
            <Text style={styles.statLbl}>Completed</Text>
          </View>
        </View>
      </LinearGradient>

      <View style={styles.body}>
        {next && (
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Up next</Text>
            <TouchableOpacity
              style={styles.nextCard}
              onPress={() => navigation.navigate('Attendance', { lesson: next, date: next.date })}
              activeOpacity={0.85}
            >
              <View style={styles.nextLeft}>
                <View style={styles.nextAvatar}>
                  <Text style={styles.nextAvatarText}>
                    {(next.student_name || '?').trim().split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()}
                  </Text>
                </View>
                <View>
                  <Text style={styles.nextName}>{next.student_name}</Text>
                  <Text style={styles.nextTime}>{formatTime(next.start)} · {next.duration_minutes || 60} min</Text>
                </View>
              </View>
              <View style={styles.nextAction}>
                <Text style={styles.nextActionText}>Record</Text>
              </View>
            </TouchableOpacity>
          </View>
        )}

        {lessons.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyEmoji}>🎉</Text>
            <Text style={styles.emptyTitle}>No lessons today</Text>
            <Text style={styles.emptySub}>Enjoy your day off!</Text>
          </View>
        ) : (
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>All lessons today</Text>
            {lessons.map((lesson, i) => (
              <TouchableOpacity
                key={i}
                style={styles.lessonCard}
                onPress={() => !lesson.status && navigation.navigate('Attendance', { lesson, date: lesson.date })}
                activeOpacity={lesson.status ? 1 : 0.75}
              >
                <View style={styles.timeCol}>
                  <Text style={styles.timeText}>{formatTime(lesson.start)}</Text>
                </View>
                <View style={styles.lessonInfo}>
                  <Text style={styles.lessonName}>{lesson.student_name}</Text>
                  <Text style={styles.lessonDur}>{lesson.duration_minutes || 60} min</Text>
                </View>
                {lesson.status
                  ? <StatusPill status={lesson.status} />
                  : <Text style={styles.tapHint}>Tap →</Text>
                }
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:      { flex: 1, backgroundColor: COLORS.bg },
  center:         { flex: 1, justifyContent: 'center', alignItems: 'center' },
  hero:           { paddingTop: 20, paddingBottom: 32, paddingHorizontal: 24 },
  heroDate:       { fontSize: 13, color: 'rgba(255,255,255,0.6)', fontWeight: '500', marginBottom: 4 },
  heroTitle:      { fontSize: 26, fontWeight: '800', color: '#fff', marginBottom: 24 },
  statsRow:       { flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 16, padding: 16 },
  statBox:        { flex: 1, alignItems: 'center' },
  statNum:        { fontSize: 28, fontWeight: '800', color: '#fff' },
  statLbl:        { fontSize: 11, color: 'rgba(255,255,255,0.65)', marginTop: 2, fontWeight: '500' },
  statDivider:    { width: 1, backgroundColor: 'rgba(255,255,255,0.2)' },
  body:           { padding: 20 },
  section:        { marginBottom: 24 },
  sectionLabel:   { fontSize: 11, fontWeight: '700', color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 12 },
  nextCard:       { backgroundColor: '#fff', borderRadius: 18, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1, borderColor: COLORS.border, ...SHADOW_CARD },
  nextLeft:       { flexDirection: 'row', alignItems: 'center', gap: 14 },
  nextAvatar:     { width: 46, height: 46, borderRadius: 14, backgroundColor: '#eef2ff', alignItems: 'center', justifyContent: 'center' },
  nextAvatarText: { fontSize: 16, fontWeight: '800', color: COLORS.primary },
  nextName:       { fontSize: 17, fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  nextTime:       { fontSize: 13, color: COLORS.muted },
  nextAction:     { backgroundColor: COLORS.primary, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 8 },
  nextActionText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  lessonCard:     { backgroundColor: '#fff', borderRadius: 14, padding: 14, flexDirection: 'row', alignItems: 'center', marginBottom: 8, borderWidth: 1, borderColor: COLORS.border },
  timeCol:        { width: 52, marginRight: 12 },
  timeText:       { fontSize: 13, fontWeight: '700', color: COLORS.primary },
  lessonInfo:     { flex: 1 },
  lessonName:     { fontSize: 15, fontWeight: '700', color: COLORS.text, marginBottom: 1 },
  lessonDur:      { fontSize: 12, color: COLORS.muted },
  pill:           { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 },
  pillText:       { fontSize: 11, fontWeight: '700' },
  tapHint:        { fontSize: 13, color: COLORS.muted, fontWeight: '500' },
  empty:          { alignItems: 'center', paddingVertical: 48 },
  emptyEmoji:     { fontSize: 52, marginBottom: 12 },
  emptyTitle:     { fontSize: 20, fontWeight: '800', color: COLORS.text, marginBottom: 6 },
  emptySub:       { fontSize: 15, color: COLORS.muted },
});
