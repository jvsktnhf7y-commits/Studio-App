import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, RefreshControl, ActivityIndicator, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../components/Card';
import { getTodayLessons } from '../services/api';
import { COLORS, GRADIENT, SHADOW } from '../theme';

function formatTime(isoString) {
  if (!isoString) return '';
  try {
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function BalanceBadge({ balance }) {
  const color = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;
  const bg    = balance < 0 ? COLORS.dangerBg : balance < 50 ? COLORS.warningBg : COLORS.successBg;
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color }]}>${balance.toFixed(2)}</Text>
    </View>
  );
}

export default function DashboardScreen({ navigation }) {
  const [lessons,    setLessons]    = useState([]);
  const [date,       setDate]       = useState('');
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const data = await getTodayLessons();
      if (data.ok) { setLessons(data.lessons); setDate(data.date); }
    } catch {
      Alert.alert('Error', "Failed to load today's lessons.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function renderLesson({ item }) {
    const balance = item.prepaid_balance ?? 0;
    return (
      <Card>
        <View style={styles.cardTop}>
          <View style={{ flex: 1 }}>
            <Text style={styles.studentName}>{item.student_name || item.summary}</Text>
            {item.is_registered && <BalanceBadge balance={balance} />}
            {!item.is_registered && (
              <Text style={styles.unregistered}>Not registered</Text>
            )}
          </View>
          <View style={styles.timePill}>
            <Text style={styles.timeText}>{formatTime(item.start)}</Text>
          </View>
        </View>

        {item.is_registered && (
          <TouchableOpacity
            style={styles.attendRow}
            onPress={() => navigation.navigate('Attendance', { lesson: item, date })}
            activeOpacity={0.7}
          >
            <LinearGradient colors={GRADIENT} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.attendGradient}>
              <Text style={styles.attendText}>Record Attendance  →</Text>
            </LinearGradient>
          </TouchableOpacity>
        )}
      </Card>
    );
  }

  const todayFormatted = date
    ? new Date(date + 'T12:00:00').toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })
    : '';

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={GRADIENT} style={styles.headerBanner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
        <Text style={styles.bannerDate}>{todayFormatted}</Text>
        <Text style={styles.bannerCount}>
          {lessons.length} {lessons.length === 1 ? 'lesson' : 'lessons'} scheduled
        </Text>
      </LinearGradient>

      <FlatList
        data={lessons}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderLesson}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>🎉</Text>
            <Text style={styles.emptyTitle}>All clear!</Text>
            <Text style={styles.emptyText}>No lessons scheduled for today.</Text>
          </View>
        }
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container:      { flex: 1, backgroundColor: COLORS.bg },
  center:         { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.bg },
  headerBanner:   { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 18 },
  bannerDate:     { fontSize: 16, fontWeight: '700', color: 'rgba(255,255,255,0.85)', marginBottom: 2 },
  bannerCount:    { fontSize: 26, fontWeight: '800', color: '#fff' },
  cardTop:        { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12 },
  studentName:    { fontSize: 17, fontWeight: '800', color: COLORS.text, marginBottom: 6 },
  badge:          { alignSelf: 'flex-start', borderRadius: 20, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText:      { fontSize: 13, fontWeight: '700' },
  unregistered:   { fontSize: 12, color: COLORS.muted, fontStyle: 'italic' },
  timePill:       { backgroundColor: '#ede9fe', borderRadius: 10, paddingHorizontal: 10, paddingVertical: 5, marginLeft: 10 },
  timeText:       { fontSize: 14, fontWeight: '700', color: COLORS.primary },
  attendRow:      { borderRadius: 10, overflow: 'hidden' },
  attendGradient: { paddingVertical: 10, alignItems: 'center' },
  attendText:     { color: '#fff', fontWeight: '700', fontSize: 14 },
  empty:          { alignItems: 'center', marginTop: 80 },
  emptyIcon:      { fontSize: 52, marginBottom: 12 },
  emptyTitle:     { fontSize: 20, fontWeight: '800', color: COLORS.text, marginBottom: 6 },
  emptyText:      { fontSize: 15, color: COLORS.muted },
});
