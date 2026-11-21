/**
 * Motion helpers: an element arriving (`FadeIn`), a press (`PressScale`), a list filling in (`ListItemEnter` /
 * `useListItemEnter`). Animation here explains a change — what appeared, what was pressed — and never decorates:
 * each helper runs once (on mount or on a press), never on every render and never in a loop. Timing and curves
 * come from `theme.motion`; when the user asked for reduced motion its durations are 0, so things just appear.
 * React Native's own `Animated` only: no animation library.
 */
import React, { useEffect, useRef } from 'react';
import { Animated, Platform, Pressable, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';
import { useTheme } from '../theme';

/** Opacity and transforms run on the native thread; react-native-web has no native driver and warns if asked. */
const useNativeDriver = Platform.OS !== 'web';
/** How far an entering element rises, in points: enough to read as "arriving", not as travelling. */
const RISE = 8;
/** How small a pressed element gets: feedback, not a bounce. */
const PRESSED_SCALE = 0.97;

/** The style of an element entering after `delay` ms: opacity 0 → 1 and a short rise, once, on mount. */
export function useEnterStyle(delay = 0) {
  const { theme } = useTheme();
  const { motion } = theme;
  const progress = useRef(new Animated.Value(motion.reducedMotion ? 1 : 0)).current;
  // Once per mount: a later theme change (dark mode) must not replay the entrance. Reduced motion is the one
  // exception — switched on mid-animation, the element jumps to where it ends up.
  useEffect(() => {
    if (motion.reducedMotion) {
      progress.setValue(1);
      return undefined;
    }
    const animation = Animated.timing(progress, {
      toValue: 1, duration: motion.duration.normal, delay, easing: motion.easing.emphasized, useNativeDriver,
    });
    animation.start();
    return () => animation.stop();
  }, [progress, motion.reducedMotion]);
  return {
    opacity: progress,
    transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [RISE, 0] }) }],
  };
}

/** Fades and lifts its children into place when it mounts. Wrap the piece that appeared, not the whole screen. */
export function FadeIn({ delay = 0, style, children, testID }: {
  delay?: number; style?: StyleProp<ViewStyle>; children: React.ReactNode; testID?: string;
}) {
  const enter = useEnterStyle(delay);
  return <Animated.View testID={testID} style={[style, enter]}>{children}</Animated.View>;
}

/** The entrance of the `index`th row of a list: each row a stagger later, up to `staggerLimit` rows. */
export function useListItemEnter(index: number) {
  const { theme } = useTheme();
  const { stagger, staggerLimit } = theme.motion;
  return useEnterStyle(Math.min(Math.max(index, 0), staggerLimit) * stagger);
}

/** A list row that enters in turn: for the rows of a list that just loaded, not for a row scrolled into view. */
export function ListItemEnter({ index, style, children, testID }: {
  index: number; style?: StyleProp<ViewStyle>; children: React.ReactNode; testID?: string;
}) {
  const enter = useListItemEnter(index);
  return <Animated.View testID={testID} style={[style, enter]}>{children}</Animated.View>;
}

/**
 * A pressable that shrinks a little while pressed. With reduced motion it dims instead: the press is still
 * acknowledged, nothing moves.
 */
export function PressScale({ style, children, onPressIn, onPressOut, accessibilityRole = 'button', ...rest }:
  Omit<PressableProps, 'style' | 'children'> & { style?: StyleProp<ViewStyle>; children: React.ReactNode }) {
  const { theme } = useTheme();
  const { motion } = theme;
  const pressed = useRef(new Animated.Value(0)).current;
  const to = (value: number) => Animated.timing(pressed, {
    toValue: value, duration: motion.duration.fast, easing: motion.easing.standard, useNativeDriver,
  }).start();
  const scale = pressed.interpolate({ inputRange: [0, 1], outputRange: [1, motion.reducedMotion ? 1 : PRESSED_SCALE] });
  const opacity = pressed.interpolate({ inputRange: [0, 1], outputRange: [1, motion.reducedMotion ? 0.85 : 1] });
  return (
    <Pressable
      accessibilityRole={accessibilityRole}
      onPressIn={(e) => { to(1); onPressIn?.(e); }}
      onPressOut={(e) => { to(0); onPressOut?.(e); }}
      {...rest}
    >
      <Animated.View style={[style, { opacity, transform: [{ scale }] }]}>{children}</Animated.View>
    </Pressable>
  );
}
