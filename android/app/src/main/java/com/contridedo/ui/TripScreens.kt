package com.contridedo.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AccountBalanceWallet
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.NotificationsNone
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.automirrored.filled.ReceiptLong
import androidx.compose.material.icons.filled.TravelExplore
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.contridedo.data.EQUAL_SPLIT
import com.contridedo.data.EXACT_SPLIT
import com.contridedo.data.PERCENTAGE_SPLIT
import com.contridedo.data.ExpenseCreatePayload
import com.contridedo.data.buildExpenseSplits
import java.math.BigDecimal
import java.util.Locale

private val Paper = Color(0xFFFAF7F2)
private val Forest = Color(0xFF224A3E)
private val DeepForest = Color(0xFF073328)
private val Citrus = Color(0xFFD8F042)
private val Ink = Color(0xFF1B2B24)
private val MutedInk = Color(0xFF65726A)
private val Rule = Color(0xFFE3DDD3)
private val Clay = Color(0xFFC86D51)
private val SoftGreen = Color(0xFFE9EEDF)

@Composable
fun ContriDedoTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = androidx.compose.material3.lightColorScheme(
            primary = Forest,
            onPrimary = Color.White,
            secondary = Citrus,
            onSecondary = Ink,
            background = Paper,
            onBackground = Ink,
            surface = Paper,
            onSurface = Ink,
            surfaceVariant = Color(0xFFF0EDE9),
            onSurfaceVariant = MutedInk,
            outline = Rule,
            error = Color(0xFF9E3D32),
        ),
        content = content,
    )
}

data class TripCardData(
    val id: Long,
    val title: String,
    val destination: String,
    val dates: String,
    val totalSpent: String,
    val travelers: Int,
    val balance: String,
    val isActive: Boolean,
)

data class ExpenseParticipant(
    val id: Long,
    val name: String,
    val initials: String,
    val tint: Color,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TripListScreen(
    trips: List<TripCardData>,
    selectedTripId: Long,
    onTripSelected: (TripCardData) -> Unit,
    onAddTrip: () -> Unit,
    onAddExpense: () -> Unit,
    onActivity: () -> Unit,
    onBalances: () -> Unit,
    onProfile: () -> Unit,
) {
    Scaffold(
        containerColor = Paper,
        contentWindowInsets = WindowInsets.navigationBars,
        topBar = {
            TopAppBar(
                title = { Wordmark() },
                actions = {
                    IconButton(onClick = onActivity) {
                        Icon(Icons.Default.NotificationsNone, contentDescription = "Notifications")
                    }
                    Spacer(Modifier.width(8.dp))
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Paper,
                    titleContentColor = Ink,
                    actionIconContentColor = Forest,
                ),
            )
        },
        bottomBar = {
            NavigationBar(containerColor = Paper, tonalElevation = 0.dp) {
                NavigationBarItem(
                    selected = true,
                    onClick = {},
                    icon = { Icon(Icons.Default.TravelExplore, contentDescription = null) },
                    label = { Text("Trips") },
                )
                NavigationBarItem(
                    selected = false,
                    onClick = onActivity,
                    icon = { Icon(Icons.AutoMirrored.Filled.ReceiptLong, contentDescription = null) },
                    label = { Text("Activity") },
                )
                NavigationBarItem(
                    selected = false,
                    onClick = onBalances,
                    icon = { Icon(Icons.Default.AccountBalanceWallet, contentDescription = null) },
                    label = { Text("Balances") },
                )
                NavigationBarItem(
                    selected = false,
                    onClick = onProfile,
                    icon = { Icon(Icons.Default.Person, contentDescription = null) },
                    label = { Text("Profile") },
                )
            }
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(
                start = 20.dp,
                top = 16.dp,
                end = 20.dp,
                bottom = 22.dp,
            ),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Text("YOUR TRAVEL JOURNAL", color = MutedInk, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.4.sp)
                Spacer(Modifier.height(8.dp))
                Text("Good morning, Nadia", style = MaterialTheme.typography.headlineMedium.copy(fontFamily = FontFamily.Serif), color = DeepForest)
                Text("A clear tab makes a lighter trip.", color = MutedInk, fontSize = 13.sp)
            }
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    JournalStat("ACTIVE TRIPS", "1")
                    JournalStat("COMING YOUR WAY", "$342.88", accent = true)
                }
            }
            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Your trips", style = MaterialTheme.typography.titleLarge.copy(fontFamily = FontFamily.Serif), color = Ink)
                        Text("Every plan, one shared ledger", color = MutedInk, fontSize = 11.sp)
                    }
                    IconButton(onClick = onAddTrip) {
                        Icon(Icons.Default.Add, contentDescription = "Create a trip", tint = Forest)
                    }
                }
            }
            items(trips, key = { it.id }) { trip ->
                TripRow(
                    trip = trip,
                    selected = trip.id == selectedTripId,
                    onClick = { onTripSelected(trip) },
                )
            }
            item {
                Button(
                    onClick = onAddExpense,
                    modifier = Modifier.fillMaxWidth().height(48.dp),
                    shape = RoundedCornerShape(4.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Forest, contentColor = Color.White),
                ) {
                    Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Add an expense", fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

@Composable
private fun RowScope.JournalStat(label: String, value: String, accent: Boolean = false) {
    Column(
        Modifier.weight(1f).background(if (accent) SoftGreen else Color.White, RoundedCornerShape(4.dp)).padding(13.dp),
        verticalArrangement = Arrangement.spacedBy(5.dp),
    ) {
        Text(label, color = MutedInk, fontSize = 8.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
        Text(value, color = if (accent) Forest else Ink, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun TripRow(trip: TripCardData, selected: Boolean, onClick: () -> Unit) {
    Column(
        Modifier.fillMaxWidth()
            .background(if (selected) Color.White else Color.Transparent, RoundedCornerShape(4.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 13.dp, vertical = 13.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(7.dp).background(if (trip.isActive) Forest else Color(0xFF97A39A), RoundedCornerShape(50)))
            Spacer(Modifier.width(8.dp))
            Text(if (trip.isActive) "CURRENT TRIP" else "PAST TRIP", color = MutedInk, fontSize = 8.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
            Spacer(Modifier.weight(1f))
            Icon(Icons.Default.ChevronRight, contentDescription = "Open ${trip.title}", tint = MutedInk, modifier = Modifier.size(18.dp))
        }
        HorizontalDivider(color = Rule)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(trip.title, color = DeepForest, fontSize = 17.sp, fontFamily = FontFamily.Serif, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("${trip.dates}  ·  ${trip.destination}", color = MutedInk, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            Text(trip.totalSpent.toCurrency(), color = Ink, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("${trip.travelers} travelers", color = MutedInk, fontSize = 10.sp)
            Spacer(Modifier.weight(1f))
            Text(trip.balance, color = if (trip.isActive) Forest else MutedInk, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddExpenseScreen(
    tripId: Long,
    tripName: String,
    members: List<ExpenseParticipant>,
    onBack: () -> Unit,
    onSaveExpense: (Long, ExpenseCreatePayload) -> Unit,
) {
    var description by remember { mutableStateOf("") }
    var totalAmount by remember { mutableStateOf("") }
    var payerId by remember { mutableStateOf(members.firstOrNull()?.id ?: 0L) }
    var payerMenuOpen by remember { mutableStateOf(false) }
    var calculationMethod by remember { mutableStateOf(EQUAL_SPLIT) }
    var selectedIds by remember { mutableStateOf(members.map { it.id }) }
    val values = remember(members) {
        mutableStateMapOf<Long, String>().apply {
            members.forEach { put(it.id, "") }
        }
    }
    var submitError by remember { mutableStateOf("") }

    val splits = remember(totalAmount, selectedIds, calculationMethod, values.toMap()) {
        runCatching {
            buildExpenseSplits(totalAmount, selectedIds, calculationMethod, values.toMap())
        }.getOrNull()
    }
    val amountLabel = totalAmount.toCurrencyOrPlaceholder()
    val totalIsValid = runCatching { totalAmount.toBigDecimal() > BigDecimal.ZERO }.getOrDefault(false)

    Scaffold(
        containerColor = Paper,
        contentWindowInsets = WindowInsets.navigationBars,
        topBar = {
            TopAppBar(
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                title = { Text("Add an expense", fontSize = 17.sp, fontWeight = FontWeight.SemiBold) },
                actions = {
                    IconButton(onClick = onBack) { Icon(Icons.Default.Close, contentDescription = "Close") }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Paper),
            )
        },
        bottomBar = {
            Surface(color = Paper, shadowElevation = 2.dp, contentColor = Ink) {
                Button(
                    onClick = {
                        val safeSplits = splits
                        if (description.isBlank()) {
                            submitError = "Add a short description first."
                        } else if (!totalIsValid || safeSplits == null) {
                            submitError = "Check the amount and make sure all shares add up."
                        } else {
                            submitError = ""
                            onSaveExpense(
                                tripId,
                                ExpenseCreatePayload(
                                    description = description.trim(),
                                    totalAmount = totalAmount.toCanonicalMoney(),
                                    payerId = payerId,
                                    splits = safeSplits,
                                ),
                            )
                        }
                    },
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 12.dp).height(48.dp),
                    shape = RoundedCornerShape(4.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Citrus, contentColor = Ink),
                ) {
                    Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Save expense  ·  $amountLabel", fontWeight = FontWeight.Bold)
                }
            }
        },
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).imePadding().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(15.dp),
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.padding(top = 4.dp)) {
                Text("FIELD NOTE  ·  EXPENSE ENTRY", color = MutedInk, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                Text(tripName, color = Forest, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
            }
            OutlinedTextField(
                value = description,
                onValueChange = { description = it; submitError = "" },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Description") },
                placeholder = { Text("Morning campfire coffee") },
                singleLine = true,
                shape = RoundedCornerShape(4.dp),
            )
            OutlinedTextField(
                value = totalAmount,
                onValueChange = { totalAmount = it.filter { char -> char.isDigit() || char == '.' }; submitError = "" },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Total amount (USD)") },
                leadingIcon = { Text("$", color = Forest, fontWeight = FontWeight.SemiBold) },
                trailingIcon = { Text("USD", color = MutedInk, fontSize = 10.sp, modifier = Modifier.padding(end = 12.dp)) },
                placeholder = { Text("0.00") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                shape = RoundedCornerShape(4.dp),
                supportingText = { Text("Use a two-decimal amount, such as 10.00") },
            )
            Box {
                val payer = members.firstOrNull { it.id == payerId }?.name ?: "Choose a payer"
                OutlinedTextField(
                    value = payer,
                    onValueChange = {},
                    modifier = Modifier.fillMaxWidth().clickable { payerMenuOpen = true },
                    readOnly = true,
                    label = { Text("Paid by") },
                    trailingIcon = { Icon(Icons.Default.ExpandMore, contentDescription = "Choose payer") },
                    shape = RoundedCornerShape(4.dp),
                )
                DropdownMenu(expanded = payerMenuOpen, onDismissRequest = { payerMenuOpen = false }) {
                    members.forEach { member ->
                        DropdownMenuItem(
                            text = { Text(member.name) },
                            onClick = { payerId = member.id; payerMenuOpen = false },
                        )
                    }
                }
            }
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("SPLIT METHOD", color = MutedInk, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    listOf(EQUAL_SPLIT to "Equal", PERCENTAGE_SPLIT to "Percentage", EXACT_SPLIT to "Exact").forEach { (method, label) ->
                        FilterChip(
                            selected = calculationMethod == method,
                            onClick = { calculationMethod = method; submitError = "" },
                            label = { Text(label, fontSize = 11.sp) },
                            leadingIcon = if (calculationMethod == method) ({ Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(15.dp)) }) else null,
                        )
                    }
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("SPLIT BETWEEN", color = MutedInk, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Text("${selectedIds.size} of ${members.size} travelers", color = MutedInk, fontSize = 10.sp)
                }
                TextButtonLike(
                    text = if (selectedIds.size == members.size) "Deselect all" else "Select all",
                    onClick = {
                        selectedIds = if (selectedIds.size == members.size) emptyList() else members.map { it.id }
                    },
                )
            }
            Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
                members.forEach { member ->
                    val selected = member.id in selectedIds
                    val share = splits?.firstOrNull { it.userId == member.id }?.amountOwed
                    Row(
                        Modifier.fillMaxWidth().heightIn(min = 54.dp).clickable {
                            selectedIds = if (selected) selectedIds - member.id else selectedIds + member.id
                            submitError = ""
                        }.padding(vertical = 5.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Checkbox(checked = selected, onCheckedChange = { checked ->
                            selectedIds = if (checked) selectedIds + member.id else selectedIds - member.id
                            submitError = ""
                        })
                        Surface(color = member.tint, shape = RoundedCornerShape(4.dp), modifier = Modifier.size(34.dp)) {
                            Box(contentAlignment = Alignment.Center) { Text(member.initials, color = Ink, fontSize = 10.sp, fontWeight = FontWeight.Bold) }
                        }
                        Spacer(Modifier.width(9.dp))
                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Text(member.name, color = Ink, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                            Text(if (selected) "Traveler #${member.id}" else "Not included", color = MutedInk, fontSize = 9.sp)
                        }
                        if (selected && calculationMethod != EQUAL_SPLIT) {
                            OutlinedTextField(
                                value = values[member.id].orEmpty(),
                                onValueChange = { values[member.id] = it.filter { char -> char.isDigit() || char == '.' }; submitError = "" },
                                modifier = Modifier.width(92.dp),
                                placeholder = { Text(if (calculationMethod == EXACT_SPLIT) "0.00" else "0%", fontSize = 10.sp) },
                                suffix = if (calculationMethod == PERCENTAGE_SPLIT) ({ Text("%", fontSize = 10.sp) }) else null,
                                singleLine = true,
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                                shape = RoundedCornerShape(4.dp),
                            )
                        } else {
                            Text(if (selected) "${share?.let { "$$it" } ?: "—"}" else "$0.00", color = if (selected) Forest else MutedInk, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                    HorizontalDivider(color = Rule)
                }
            }
            Column(Modifier.fillMaxWidth().background(SoftGreen, RoundedCornerShape(4.dp)).padding(13.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Allocated", color = MutedInk, fontSize = 11.sp, modifier = Modifier.weight(1f))
                    Text(splits?.sumOf { it.amountOwed.toBigDecimal() }?.let { "$$it" } ?: "Check split", color = Forest, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    Text(" of $amountLabel", color = MutedInk, fontSize = 10.sp)
                }
                Text(
                    when {
                        splits == null -> "${if (calculationMethod == PERCENTAGE_SPLIT) "Percentages must total 100%." else "Shares must match the total."}"
                        calculationMethod == EQUAL_SPLIT -> "Any remainder cents go to the first travelers listed."
                        else -> "Balanced and matches the expense total."
                    },
                    color = if (splits == null) Clay else MutedInk,
                    fontSize = 9.sp,
                )
            }
            if (submitError.isNotBlank()) {
                Text(submitError, color = MaterialTheme.colorScheme.error, fontSize = 11.sp)
            }
            Spacer(Modifier.height(10.dp))
        }
    }
}

@Composable
private fun Wordmark() {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Box(Modifier.size(30.dp).background(Forest, RoundedCornerShape(topStart = 10.dp, topEnd = 10.dp, bottomEnd = 10.dp, bottomStart = 2.dp)), contentAlignment = Alignment.Center) {
            Text("c", color = Paper, fontFamily = FontFamily.Serif, fontSize = 22.sp)
        }
        Text("contri", color = Ink, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Surface(color = Citrus, shape = RoundedCornerShape(2.dp)) {
            Text("Dedo", color = Ink, fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 3.dp, vertical = 1.dp))
        }
    }
}

@Composable
private fun TextButtonLike(text: String, onClick: () -> Unit) {
    Text(text, color = Forest, fontSize = 10.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickable(onClick = onClick).padding(8.dp))
}

private fun String.toCurrency(): String = runCatching {
    val value = BigDecimal(this)
    "$" + String.format(Locale.US, "%,.2f", value)
}.getOrDefault("$0.00")

private fun String.toCurrencyOrPlaceholder(): String = runCatching {
    "$" + String.format(Locale.US, "%,.2f", BigDecimal(this))
}.getOrDefault("$0.00")

private fun String.toCanonicalMoney(): String = runCatching {
    BigDecimal(trim()).setScale(2).toPlainString()
}.getOrDefault(trim())
