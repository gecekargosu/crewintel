import React, { useState } from 'react';
import { View, TextInput, Text, StyleSheet, ViewStyle, TouchableOpacity } from 'react-native';
import { useTheme } from '../../hooks/useTheme';

interface InputProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric' | 'phone-pad';
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  error?: string;
  multiline?: boolean;
  numberOfLines?: number;
  style?: ViewStyle;
  editable?: boolean;
  rightIcon?: React.ReactNode;
}

export default function Input({
  label,
  value,
  onChangeText,
  placeholder,
  secureTextEntry = false,
  keyboardType = 'default',
  autoCapitalize = 'none',
  error,
  multiline = false,
  numberOfLines = 1,
  style,
  editable = true,
  rightIcon,
}: InputProps) {
  const { colors } = useTheme();
  const [focused, setFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(secureTextEntry);

  return (
    <View style={[styles.container, style]}>
      <Text style={[styles.label, { color: colors.text }]}>{label}</Text>
      <View
        style={[
          styles.inputWrapper,
          {
            backgroundColor: colors.inputBg,
            borderColor: error ? colors.danger : focused ? colors.tint : colors.inputBorder,
            borderWidth: focused ? 1.5 : 1,
          },
          multiline && { height: numberOfLines * 24 + 24, alignItems: 'flex-start' },
        ]}
      >
        <TextInput
          style={[
            styles.input,
            { color: colors.text },
            multiline && { textAlignVertical: 'top' },
            !editable && { opacity: 0.5 },
          ]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.grey400}
          secureTextEntry={showPassword}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          editable={editable}
          multiline={multiline}
          numberOfLines={numberOfLines}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
        {secureTextEntry && (
          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            style={styles.eyeButton}
          >
            <Text style={{ color: colors.grey500, fontSize: 16 }}>
              {showPassword ? '👁️' : '👁️‍🗨️'}
            </Text>
          </TouchableOpacity>
        )}
        {rightIcon && <View style={styles.eyeButton}>{rightIcon}</View>}
      </View>
      {error && <Text style={[styles.error, { color: colors.danger }]}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 10,
    paddingHorizontal: 14,
  },
  input: {
    flex: 1,
    height: 44,
    fontSize: 15,
  },
  eyeButton: {
    paddingLeft: 10,
    paddingVertical: 10,
  },
  error: {
    fontSize: 12,
    marginTop: 4,
  },
});
