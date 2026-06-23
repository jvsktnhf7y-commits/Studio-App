import React from 'react';
import { View, StyleSheet } from 'react-native';
import { SHADOW_SM } from '../theme';

export default function Card({ children, style }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    ...SHADOW_SM,
  },
});
