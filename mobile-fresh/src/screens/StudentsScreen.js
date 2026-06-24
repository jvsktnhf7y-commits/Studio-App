import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, FlatList, TextInput, TouchableOpacity,
  StyleSheet, RefreshControl, ActivityIndicator, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Card from '../components/Card';
import { getStudents } from '../services/api';
import { COLORS, GRADIENT } from '../theme';

function Avatar({ name }) {
  const initials = name.trim().split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  return (
    <LinearGradient colors={GRADIENT} style={styles.avatar} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
      <Text style={styles.avatarText}>{initials}</Text>
    </LinearGradient>
  );
}

function BalanceChip({ balance }) {
  const color = balance < 0 ? COLORS.danger : balance < 50 ? COLORS.warning : COLORS.success;
  const bg    = balance < 0 ? COLORS.dangerBg : balance < 50 ? COLORS.warningBg : COLORS.successBg;
  return (
    <View style={[styles.chip, { backgroundColor: bg }]}>
      <Text style={[styles.chipText, { color }]}>${balance.toFixed(2)}</Text>
    </View>
  );
}

export default function StudentsScreen({ navigation }) {
  const [all,        setAll]        = useState([]);
  const [filtered,   setFiltered]   = useState([]);
  const [query,      setQuery]      = useState('');
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const data = await getStudents();
      if (data.ok) { setAll(data.students); setFiltered(data.students); }
    } catch {
      Alert.alert('Error', 'Failed to load students.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function search(text) {
    setQuery(text);
    const q = text.toLowerCase();
    setFiltered(q ? all.filter(s => s.name.toLowerCase().includes(q)) : all);
  }

  function renderStudent({ item }) {
    const balance = item.prepaid_balance ?? 0;
    return (
      <TouchableOpacity
        activeOpacity={0.75}
        onPress={() => navigation.navigate('StudentProfile', { name: item.name })}
      >
        <Card style={styles.studentCard}>
          <View style={styles.cardRow}>
            <Avatar name={item.name} />
            <View style={styles.cardInfo}>
              <Text style={styles.name}>{item.name}</Text>
              <Text style={styles.tier}>{item.tier || 'No tier'} · ${item.rate}/hr</Text>
            </View>
            <BalanceChip balance={balance} />
          </View>
          {item.target_minutes > 0 && (
            <View style={styles.minutesRow}>
              <View style={styles.minuteBar}>
                <LinearGradient colors={GRADIENT} style={[styles.minuteFill, { width: '60%' }]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} />
              </View>
              <Text style={styles.minuteLabel}>{item.target_minutes} min/wk target</Text>
            </View>
          )}
        </Card>
      </TouchableOpacity>
    );
  }

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  return (
    <View style={styles.container}>
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="Search students…"
          placeholderTextColor={COLORS.muted}
          value={query}
          onChangeText={search}
          clearButtonMode="while-editing"
        />
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.name}
        renderItem={renderStudent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />
        }
        ListHeaderComponent={
          !query && all.length > 0
            ? <Text style={styles.countLabel}>{all.length} students</Text>
            : null
        }
        ListEmptyComponent={
          <Text style={styles.empty}>No students found.</Text>
        }
        contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('Payment', {})}
        activeOpacity={0.85}
      >
        <LinearGradient colors={GRADIENT} style={styles.fabGrad} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
          <Text style={styles.fabText}>💳  Payment</Text>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: COLORS.bg },
  center:      { flex: 1, justifyContent: 'center', alignItems: 'center' },
  searchWrap:  { flexDirection: 'row', alignItems: 'center', margin: 16, marginBottom: 8, backgroundColor: '#fff', borderRadius: 14, paddingHorizontal: 14, borderWidth: 1.5, borderColor: COLORS.border },
  searchIcon:  { fontSize: 16, marginRight: 8 },
  searchInput: { flex: 1, height: 46, fontSize: 15, color: COLORS.text },
  countLabel:  { fontSize: 13, fontWeight: '600', color: COLORS.muted, marginBottom: 8, marginLeft: 2 },
  studentCard: { padding: 14 },
  cardRow:     { flexDirection: 'row', alignItems: 'center' },
  avatar:      { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  avatarText:  { color: '#fff', fontWeight: '800', fontSize: 16 },
  cardInfo:    { flex: 1 },
  name:        { fontSize: 16, fontWeight: '800', color: COLORS.text, marginBottom: 2 },
  tier:        { fontSize: 13, color: COLORS.subtext },
  chip:        { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 },
  chipText:    { fontSize: 13, fontWeight: '700' },
  minutesRow:  { marginTop: 10, flexDirection: 'row', alignItems: 'center', gap: 10 },
  minuteBar:   { flex: 1, height: 5, backgroundColor: COLORS.bg, borderRadius: 10, overflow: 'hidden' },
  minuteFill:  { height: '100%', borderRadius: 10 },
  minuteLabel: { fontSize: 11, color: COLORS.muted, flexShrink: 0 },
  empty:       { textAlign: 'center', color: COLORS.muted, marginTop: 60, fontSize: 15 },
  fab:         { position: 'absolute', bottom: 24, right: 20, borderRadius: 28, overflow: 'hidden', elevation: 6, shadowColor: '#667eea', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.35, shadowRadius: 12 },
  fabGrad:     { paddingHorizontal: 22, paddingVertical: 14, flexDirection: 'row', alignItems: 'center' },
  fabText:     { color: '#fff', fontWeight: '800', fontSize: 15 },
});
