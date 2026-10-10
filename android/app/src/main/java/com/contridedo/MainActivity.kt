package com.contridedo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import com.contridedo.data.ExpenseApi
import com.contridedo.data.ExpenseCreatePayload
import com.contridedo.ui.AddExpenseScreen
import com.contridedo.ui.ContriDedoTheme
import com.contridedo.ui.ExpenseParticipant
import com.contridedo.ui.TripCardData
import com.contridedo.ui.TripListScreen
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

private val tripMembers = listOf(
    ExpenseParticipant(101, "Nadia Chen", "NC", Color(0xFFD9E9DC)),
    ExpenseParticipant(102, "Marco Silva", "MS", Color(0xFFF4D9C7)),
    ExpenseParticipant(103, "Elena Rostova", "ER", Color(0xFFD9E2F2)),
    ExpenseParticipant(104, "Devon Vance", "DV", Color(0xFFF2E6B9)),
    ExpenseParticipant(105, "Maya Patel", "MP", Color(0xFFE6DCEF)),
)

private val tripSamples = listOf(
    TripCardData(42, "Hudson Valley Weekend", "Gardiner & Beacon, NY", "Oct 12–15", "2845.60", 5, "You get back $342.88", true),
    TripCardData(43, "Banff Camper Run", "Alberta, Canada", "Aug 2024", "0.00", 4, "Settled", false),
    TripCardData(44, "Maine Coast Haven", "Portland, ME", "Jun 2024", "0.00", 4, "Settled", false),
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ContriDedoTheme {
                val scope = rememberCoroutineScope()
                val snackbarHostState = remember { SnackbarHostState() }
                val api = remember { ExpenseApi.create(BuildConfig.API_BASE_URL) }
                var selectedTrip by remember { mutableStateOf(tripSamples.first()) }
                var showAddExpense by remember { mutableStateOf(false) }
                var savingExpense by remember { mutableStateOf(false) }
                // One key per payload so a retry after a failure cannot create a duplicate expense.
                var lastAttempt by remember { mutableStateOf<Pair<ExpenseCreatePayload, String>?>(null) }

                Box(Modifier.fillMaxSize()) {
                    if (showAddExpense) {
                        AddExpenseScreen(
                            tripId = selectedTrip.id,
                            tripName = selectedTrip.title,
                            members = tripMembers,
                            onBack = { showAddExpense = false },
                            onSaveExpense = { tripId, payload ->
                                if (!savingExpense) {
                                    savingExpense = true
                                    val key = lastAttempt?.takeIf { it.first == payload }?.second
                                        ?: UUID.randomUUID().toString()
                                    lastAttempt = payload to key
                                    scope.launch {
                                        try {
                                            val response = api.createExpense(tripId, payload, key)
                                            if (response.isSuccessful) {
                                                showAddExpense = false
                                                lastAttempt = null
                                                snackbarHostState.showSnackbar("Expense added to ${selectedTrip.title}.")
                                            } else {
                                                snackbarHostState.showSnackbar("Could not save expense (${response.code()}).")
                                            }
                                        } catch (cancelled: CancellationException) {
                                            throw cancelled
                                        } catch (_: Exception) {
                                            snackbarHostState.showSnackbar("Could not reach the contriDedo API.")
                                        } finally {
                                            savingExpense = false
                                        }
                                    }
                                }
                            },
                        )
                    } else {
                        TripListScreen(
                            trips = tripSamples,
                            selectedTripId = selectedTrip.id,
                            onTripSelected = { selectedTrip = it },
                            onAddTrip = { scope.launch { snackbarHostState.showSnackbar("Trip creation is coming soon.") } },
                            onAddExpense = { showAddExpense = true },
                            onActivity = { scope.launch { snackbarHostState.showSnackbar("Trip activity is up to date.") } },
                            onBalances = { scope.launch { snackbarHostState.showSnackbar("Your trip balances are ready.") } },
                            onProfile = { scope.launch { snackbarHostState.showSnackbar("Profile settings are coming soon.") } },
                        )
                    }
                    SnackbarHost(hostState = snackbarHostState, modifier = Modifier.align(Alignment.BottomCenter))
                }
            }
        }
    }
}
