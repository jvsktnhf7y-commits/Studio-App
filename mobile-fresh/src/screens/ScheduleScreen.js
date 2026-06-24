import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, FlatList, SectionList, TouchableOpacity,
  StyleSheet, RefreshControl, ActivityIndicator, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../components/Card';
import { getSchedule } from '../services/api';
import { COLORS, GRADIENT, SHADOW_SM } from '../theme';

function formatTime(isoString) {
  if (!isoString) return '';
  try {
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

function formatSectionDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = Math.round((d - today) / 86400000);
  const label = diff === 0 ? 'Today' : diff === 1 ? 'Tomorrow' : null;
  const weekday = d.toLocaleDateString([], { weekday: 'long' });
  const date    = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  return label ? `${label} · ${date}` : `${weekday} · ${date}`;
}

export default function ScheduleScreen({ navigation }) {
  const [sections,   setSections]   = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const data = await getSchedule();
      if (data.ok) {
        setSections(data.days.map(d => ({ title: d.date, data: d.lessons })));
      }
    } catch {
      Alert.alert('Error', 'Failed to load schedule.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function renderItem({ item, section }) {
    const balance      = item.prepaid_balance ?? 0;
    const balanceColor = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;
    const balanceBg    = balance < 0 ? COLORS.dangerBg : balance < 50 ? COLORS.warningBg : COLORS.successBg;
    return (
      <Card style={styles.lessonCard}>
        <View style={styles.row}>
          <View style={styles.timePill}>
            <Text style={styles.timeText}>{formatTime(item.start)}</Text>
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={styles.studentName}>{item.student_name || item.summary}</Text>
            {item.is_registered ? (
              <View style={[styles.balanceChip, { backgroundColor: balanceBg }]}>
                <Text style={[styles.balanceText, { color: balanceColor }]}>${balance.toFixed(2)}</Text>
              </View>
            ) : (
              <Text style={styles.unregistered}>Not registered</Text>
            )}
          </View>
          {item.is_registered && (
            <TouchableOpacity
              onPress={() => navigation.navigate('Attendance', { lesson: item, date: section.title })}
              activeOpacity={0.75}
            >
              <LinearGradient colors={GRADIENT} style={styles.attendBtn} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
                <Text style={styles.attendBtnText}>✓</Text>
              </LinearGradient>
            </TouchableOpacity>
          )}
        </View>
      </Card>
    );
  }

  function renderSectionHeader({ section }) {
    return (
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{formatSectionDate(section.title)}</Text>
      </View>
    );
  }

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  return (
    <View style={styles.container}>
      <SectionList
        sections={sections}
        keyExtractor={(item, i) => `${item.student_name}-${i}`}
        renderItem={renderItem}
        renderSectionHeader={renderSectionHeader}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>📅</Text>
            <Text style={styles.emptyTitle}>No upcoming lessons</Text>
            <Text style={styles.emptyText}>Nothing scheduled in the next 14 days.</Text>
          </View>
        }
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        stickySectionHeadersEnabled={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: COLORS.bg },
  center:       { flex: 1, justifyContent: 'center', alignItems: 'center' },
  sectionHeader:{ marginTop: 16, marginBottom: 6 },
  sectionTitle: { fontSize: 13, fontWeight: '700', color: COLORS.primary, textTransform: 'uppercase', letterSpacing: 0.8 },
  lessonCard:   { padding: 12, marginBottom: 8 },
  row:          { flexDirection: 'row', alignItems: 'center' },
  timePill:     { backgroundColor: '#ede9fe', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, minWidth: 54, alignItems: 'center' },
  timeText:     { fontSize: 13, fontWeight: '700', color: COLORS.primary },
  studentName:  { fontSize: 15, fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  balanceChip:  { alignSelf: 'flex-start', borderRadius: 20, paddingHorizontal: 8, paddingVertical: 2 },
  balanceText:  { fontSize: 12, fontWeight: '700' },
  unregistered: { fontSize: 12, color: COLORS.muted, fontStyle: 'italic' },
  attendBtn:    { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  attendBtnText:{ color: '#fff', fontWeight: '800', fontSize: 16 },
  empty:        { alignItems: 'center', marginTop: 80 },
  emptyIcon:    { fontSize: 52, marginBottom: 12 },
  emptyTitle:   { fontSize: 20, fontWeight: '800', color: COLORS.text, marginBottom: 6 },
  emptyText:    { fontSize: 15, color: COLORS.muted },
});
