# HisabKitab AI Backend Integration Guide for React Native

This guide provides step-by-step instructions, complete TypeScript code, and UI integration patterns to connect the **HisabKitab Expo / React Native** application with the **FastAPI AI Backend**.

---

## 1. High-Level Integration Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    HisabKitab Mobile UI                     │
│  (AI Planning Modal / Screen styled with Liquid Glass)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ User inputs: Budget, Duration,
                               │ People, Goal, Preferences
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 src/services/aiPlanService.ts               │
│  - Builds PlanningRequestPayload                            │
│  - Calls POST /api/v1/ai/generate-plan                      │
│  - Attaches Appwrite JWT (if user is logged in)             │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8000)                 │
│  - Enforces Rate Limits & Input Validation                  │
│  - Calls Google Gemini (google-genai SDK)                   │
│  - Validates & balances arithmetic deterministically        │
└──────────────────────────────┬──────────────────────────────┘
                               │ Returns PlanningResponse
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Plan Result Review                    │
│  - Displays Summary, Category Allocations, Weekly Plan, Tips│
│  - User taps "Apply to My Budget"                           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     BudgetContext                           │
│  - Updates totalBudget                                      │
│  - Syncs category budgets (Food, Grocery, Bills, etc.)      │
│  - Persists to AsyncStorage (Guest) or Appwrite (Cloud)     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Environment Configuration (`UI/.env`)

In your React Native project (`HisabKitab/UI`), update `.env` or `.env.local`:

```env
# URL to your FastAPI AI Backend
# 1. iOS Simulator:
EXPO_PUBLIC_AI_API_URL=http://localhost:8000

# 2. Android Emulator:
# EXPO_PUBLIC_AI_API_URL=http://10.0.2.2:8000

# 3. Physical Device (Expo Go / Development Build):
# Replace with your computer's LAN IP (e.g., 192.168.1.15):
# EXPO_PUBLIC_AI_API_URL=http://192.168.1.15:8000
```

---

## 3. TypeScript Schema Definitions (`src/types/aiPlan.ts`)

Create a new file in your React Native project at `src/types/aiPlan.ts`:

```typescript
export interface ExistingExpensePayload {
  category: string;
  amount: number;
  description?: string;
}

export interface PlanningRequestPayload {
  budget: number;
  currency: string;
  people: number;
  duration_days: number;
  goal: string;
  categories: string[];
  preferences?: string[];
  existing_expenses?: ExistingExpensePayload[];
}

export interface BudgetAllocation {
  category: string;
  amount: number;
  percentage: number;
  reason: string;
}

export interface WeeklyPlan {
  week: number;
  budget: number;
  focus: string;
  recommendations: string[];
}

export interface PlanningTip {
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
}

export interface PlanningResponse {
  summary: string;
  total_budget: number;
  allocated_budget: number;
  remaining_budget: number;
  allocations: BudgetAllocation[];
  weekly_plan: WeeklyPlan[];
  tips: PlanningTip[];
}

export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
```

---

## 4. AI API Client Service (`src/services/aiPlanService.ts`)

Create `src/services/aiPlanService.ts` to handle network requests, timeouts, and error handling:

```typescript
import {
  PlanningRequestPayload,
  PlanningResponse,
  APIErrorResponse,
} from "../types/aiPlan";

const BASE_URL = process.env.EXPO_PUBLIC_AI_API_URL || "http://localhost:8000";
const TIMEOUT_MS = 35000; // 35 seconds

export class AIPlanError extends Error {
  code: string;
  constructor(message: string, code = "AI_REQUEST_FAILED") {
    super(message);
    this.name = "AIPlanError";
    this.code = code;
  }
}

/**
 * Call the HisabKitab AI backend to generate a personalized budget plan.
 * @param payload User planning data
 * @param userToken Optional Bearer token (Appwrite JWT session)
 */
export async function generateBudgetPlan(
  payload: PlanningRequestPayload,
  userToken?: string | null,
): Promise<PlanningResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (userToken) {
    headers["Authorization"] = `Bearer ${userToken}`;
  }

  try {
    const response = await fetch(`${BASE_URL}/api/v1/ai/generate-plan`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `Server responded with status ${response.status}`;
      let errorCode = "API_ERROR";

      try {
        const errorData: APIErrorResponse = await response.json();
        if (errorData?.error?.message) {
          errorMessage = errorData.error.message;
          errorCode = errorData.error.code;
        }
      } catch {
        // Response was not JSON
      }

      throw new AIPlanError(errorMessage, errorCode);
    }

    const data: PlanningResponse = await response.json();
    return data;
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error.name === "AbortError") {
      throw new AIPlanError(
        "Request timed out. Please check your network and try again.",
        "TIMEOUT",
      );
    }

    if (error instanceof AIPlanError) {
      throw error;
    }

    throw new AIPlanError(
      error.message || "Unable to connect to the HisabKitab AI service.",
      "NETWORK_ERROR",
    );
  }
}

/**
 * Check health status of AI service.
 */
export async function checkAIHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    const data = await response.json();
    return data?.status === "ok";
  } catch {
    return false;
  }
}
```

---

## 5. Integrating with `BudgetContext`

HisabKitab defines 7 default categories (`Food`, `Education`, `Bills`, `Doctor`, `Transport`, `Grocery`, `Others`).

Here is how you can apply the AI allocations directly into the app's budget state:

```typescript
// Helper function inside your AI screen or BudgetContext
import { PlanningResponse } from "../types/aiPlan";
import { CategoryType } from "../types/budget";

export function applyAIPlanToBudgetContext(
  plan: PlanningResponse,
  existingCategories: CategoryType[],
  setTotalBudget: (amount: number) => void,
  updateCategoryBudget: (categoryId: number, budgetAmount: number) => void,
) {
  // 1. Set the user's total budget
  setTotalBudget(plan.total_budget);

  // 2. Map AI category names to existing category IDs (case-insensitive)
  plan.allocations.forEach((alloc) => {
    const targetCat = existingCategories.find(
      (c) => c.name.toLowerCase() === alloc.category.toLowerCase(),
    );

    if (targetCat) {
      updateCategoryBudget(targetCat.id, alloc.amount);
    } else {
      // If AI recommended a category not in the 7 defaults,
      // add to "Others" or create custom category
      const othersCat = existingCategories.find(
        (c) => c.name.toLowerCase() === "others",
      );
      if (othersCat) {
        updateCategoryBudget(
          othersCat.id,
          (othersCat.budget || 0) + alloc.amount,
        );
      }
    }
  });
}
```

---

## 6. Complete UI Component: AI Planning Modal

Below is an interactive VisionOS Liquid Glass component (`AIPlannerModal.tsx`) that you can plug into the HisabKitab UI:

```tsx
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
} from "react-native";
import * as Haptics from "expo-haptics";
import { GlassCard } from "../components/GlassCard";
import { AppleIcon } from "../components/AppleIcon";
import { generateBudgetPlan } from "../services/aiPlanService";
import { PlanningResponse } from "../types/aiPlan";

interface AIPlannerModalProps {
  visible: boolean;
  onClose: () => void;
  currency: string;
  onApplyPlan: (plan: PlanningResponse) => void;
}

export const AIPlannerModal: React.FC<AIPlannerModalProps> = ({
  visible,
  onClose,
  currency,
  onApplyPlan,
}) => {
  const [budget, setBudget] = useState("150000");
  const [people, setPeople] = useState("4");
  const [durationDays, setDurationDays] = useState("30");
  const [goal, setGoal] = useState(
    "Save for emergency fund & reduce unnecessary spending",
  );
  const [preferences, setPreferences] = useState(
    "Cook at home, keep fuel expenses disciplined",
  );

  const [loading, setLoading] = useState(false);
  const [generatedPlan, setGeneratedPlan] = useState<PlanningResponse | null>(
    null,
  );

  const handleGenerate = async () => {
    const numBudget = parseFloat(budget);
    const numPeople = parseInt(people, 10);
    const numDays = parseInt(durationDays, 10);

    if (!numBudget || numBudget <= 0) {
      Alert.alert("Validation", "Please enter a valid positive budget.");
      return;
    }

    if (!goal.trim()) {
      Alert.alert("Validation", "Please specify your financial goal.");
      return;
    }

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setLoading(true);

    try {
      const plan = await generateBudgetPlan({
        budget: numBudget,
        currency,
        people: numPeople || 1,
        duration_days: numDays || 30,
        goal: goal.trim(),
        categories: [
          "Food",
          "Education",
          "Bills",
          "Doctor",
          "Transport",
          "Grocery",
          "Others",
        ],
        preferences: preferences
          ? preferences.split(",").map((p) => p.trim())
          : [],
        existing_expenses: [],
      });

      setGeneratedPlan(plan);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert(
        "AI Planning Error",
        error.message || "Failed to generate plan.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    if (!generatedPlan) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    onApplyPlan(generatedPlan);
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View className="flex-1 bg-black/80 justify-end">
        <View className="h-[90%] bg-[#0B0D17] rounded-t-3xl p-6 border-t border-white/10">
          {/* Header */}
          <View className="flex-row justify-between items-center mb-4">
            <View className="flex-row items-center space-x-2">
              <AppleIcon name="magic" size={20} color="#60A5FA" />
              <Text className="text-xl font-bold text-white">
                HisabKitab AI Planner
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} className="p-2">
              <AppleIcon name="times" size={20} color="#9CA3AF" />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            {!generatedPlan ? (
              // Step 1: Input Form
              <View className="space-y-4">
                <Text className="text-gray-400 text-sm">
                  Let AI build a disciplined spending and savings roadmap
                  tailored to your family and goals.
                </Text>

                <GlassCard variant="default">
                  <Text className="text-gray-400 text-xs mb-1">
                    TOTAL BUDGET ({currency})
                  </Text>
                  <TextInput
                    value={budget}
                    onChangeText={setBudget}
                    keyboardType="numeric"
                    placeholderTextColor="#6B7280"
                    className="text-white text-lg font-semibold"
                  />
                </GlassCard>

                <View className="flex-row space-x-3">
                  <View className="flex-1">
                    <GlassCard variant="default">
                      <Text className="text-gray-400 text-xs mb-1">
                        FAMILY MEMBERS
                      </Text>
                      <TextInput
                        value={people}
                        onChangeText={setPeople}
                        keyboardType="numeric"
                        className="text-white text-base font-semibold"
                      />
                    </GlassCard>
                  </View>
                  <View className="flex-1">
                    <GlassCard variant="default">
                      <Text className="text-gray-400 text-xs mb-1">DAYS</Text>
                      <TextInput
                        value={durationDays}
                        onChangeText={setDurationDays}
                        keyboardType="numeric"
                        className="text-white text-base font-semibold"
                      />
                    </GlassCard>
                  </View>
                </View>

                <GlassCard variant="default">
                  <Text className="text-gray-400 text-xs mb-1">
                    PRIMARY FINANCIAL GOAL
                  </Text>
                  <TextInput
                    value={goal}
                    onChangeText={setGoal}
                    multiline
                    numberOfLines={2}
                    className="text-white text-sm"
                  />
                </GlassCard>

                <GlassCard variant="default">
                  <Text className="text-gray-400 text-xs mb-1">
                    PREFERENCES / CONSTRAINTS
                  </Text>
                  <TextInput
                    value={preferences}
                    onChangeText={setPreferences}
                    placeholder="e.g. Cook at home, avoid takeout"
                    placeholderTextColor="#6B7280"
                    className="text-white text-sm"
                  />
                </GlassCard>

                <TouchableOpacity
                  onPress={handleGenerate}
                  disabled={loading}
                  className="bg-blue-600 rounded-2xl py-4 items-center mt-4 active:opacity-80"
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text className="text-white font-bold text-base">
                      Generate AI Plan
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            ) : (
              // Step 2: Display Generated Plan
              <View className="space-y-4">
                <GlassCard variant="hero">
                  <Text className="text-blue-400 text-xs font-bold uppercase tracking-wider mb-1">
                    Executive Summary
                  </Text>
                  <Text className="text-white text-sm leading-relaxed">
                    {generatedPlan.summary}
                  </Text>
                  <View className="flex-row justify-between mt-3 pt-3 border-t border-white/10">
                    <Text className="text-gray-400 text-xs">
                      Allocated: {generatedPlan.allocated_budget} {currency}
                    </Text>
                    <Text className="text-green-400 text-xs font-bold">
                      Reserve Buffer: {generatedPlan.remaining_budget}{" "}
                      {currency}
                    </Text>
                  </View>
                </GlassCard>

                {/* Category Breakdown */}
                <Text className="text-white font-bold text-base mt-2">
                  Recommended Allocations
                </Text>
                {generatedPlan.allocations.map((item, idx) => (
                  <GlassCard key={idx} variant="subtle">
                    <View className="flex-row justify-between items-center mb-1">
                      <Text className="text-white font-semibold text-sm capitalize">
                        {item.category}
                      </Text>
                      <Text className="text-blue-400 font-bold text-sm">
                        {item.amount.toLocaleString()} {currency} (
                        {item.percentage}%)
                      </Text>
                    </View>
                    <Text className="text-gray-400 text-xs">{item.reason}</Text>
                  </GlassCard>
                ))}

                {/* Strategic Tips */}
                <Text className="text-white font-bold text-base mt-2">
                  Smart Saving Tips
                </Text>
                {generatedPlan.tips.map((tip, idx) => (
                  <GlassCard key={idx} variant="default">
                    <Text className="text-yellow-400 text-xs font-bold uppercase">
                      {tip.title}
                    </Text>
                    <Text className="text-gray-300 text-xs mt-1">
                      {tip.description}
                    </Text>
                  </GlassCard>
                ))}

                {/* Action Buttons */}
                <View className="flex-row space-x-3 mt-4 mb-8">
                  <TouchableOpacity
                    onPress={() => setGeneratedPlan(null)}
                    className="flex-1 bg-white/10 rounded-2xl py-4 items-center"
                  >
                    <Text className="text-gray-300 font-semibold text-sm">
                      Modify Inputs
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={handleApply}
                    className="flex-1 bg-green-600 rounded-2xl py-4 items-center"
                  >
                    <Text className="text-white font-bold text-sm">
                      Apply to My Budget
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};
```

---

## 7. Error Handling & Edge Cases

| Scenario                            | Mobile Behavior                                                                                                                         |
| :---------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------- |
| **No Internet Connection**          | `AIPlanError (NETWORK_ERROR)` is caught; displays a friendly offline alert without crashing.                                            |
| **Rate Limit Exceeded (429)**       | Displays _"Rate limit reached. Please wait a minute before requesting another plan."_                                                   |
| **Timeout (30s exceeded)**          | Automatically aborts request; alerts user to check connection or simplify constraints.                                                  |
| **Model Allocation > Total Budget** | Backend automatically normalizes allocations proportionally before returning; React Native always receives guaranteed balanced numbers. |
