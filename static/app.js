// Dutch Tax Calculator - Frontend JavaScript

const app = {
    // API endpoints
    API_INCOME_TYPES: '/api/income-types',
    API_ASSET_TYPES: '/api/asset-types',
    API_ALLOCATION_STRATEGIES: '/api/allocation-strategies',
    API_CALCULATE: '/api/calculate',

    // State
    incomeTypes: [],
    assetTypes: [],
    allocationStrategies: [],
    currentMemberCount: 1,

    // Initialize the app
    init() {
        console.log('Initializing Dutch Tax Calculator app...');
        this.cacheElements();
        this.loadTypes();
        this.attachEventListeners();
        this.renderMembers(1);
        console.log('✓ App initialized');
    },

    // Cache DOM elements
    cacheElements() {
        this.form = document.getElementById('taxForm');
        this.memberCount = document.getElementById('memberCount');
        this.membersContainer = document.getElementById('membersContainer');
        this.taxForm = document.getElementById('taxForm');
        this.resultsSection = document.getElementById('resultsSection');
        this.emptyState = document.getElementById('emptyState');
        this.allocationStrategy = document.getElementById('allocationStrategy');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.clearBtn = document.getElementById('clearBtn');
        this.loadJsonFile = document.getElementById('loadJsonFile');
        this.loadJsonBtn = document.getElementById('loadJsonBtn');
    },

    // Load income and asset types from API
    async loadTypes() {
        try {
            const [incomeRes, assetRes] = await Promise.all([
                fetch(this.API_INCOME_TYPES),
                fetch(this.API_ASSET_TYPES)
            ]);

            if (!incomeRes.ok || !assetRes.ok) {
                throw new Error(`Income types: ${incomeRes.status}, Asset types: ${assetRes.status}`);
            }

            this.incomeTypes = (await incomeRes.json()).types;
            this.assetTypes = (await assetRes.json()).types;
            console.log('✓ Types loaded:', this.incomeTypes.length, 'income types,', this.assetTypes.length, 'asset types');
        } catch (error) {
            console.error('✗ Error loading types:', error);
            alert('Waarschuwing: formulieropties konden niet worden geladen. Sommige functies werken mogelijk niet.');
        }
    },

    // Attach event listeners
    attachEventListeners() {
        this.memberCount.addEventListener('change', (e) => {
            this.renderMembers(parseInt(e.target.value));
        });

        this.taxForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.calculateTaxes();
        });

        this.clearBtn.addEventListener('click', () => {
            this.clearResults();
        });

        if (this.loadJsonBtn) {
            this.loadJsonBtn.addEventListener('click', () => {
                this.loadJsonIntoForm();
            });
        }
    },

    // Load a previously saved JSON submission into the current form.
    async loadJsonIntoForm() {
        if (!this.loadJsonFile || !this.loadJsonFile.files || this.loadJsonFile.files.length === 0) {
            alert('Selecteer eerst een JSON-bestand.');
            return;
        }

        const file = this.loadJsonFile.files[0];
        try {
            const text = await file.text();
            const parsed = JSON.parse(text);

            // Accept both wrapped format ({ saved_at, data }) and raw payload.
            const payload = parsed.data ? parsed.data : parsed;
            this.populateFormFromData(payload);
            alert('JSON succesvol geladen in het formulier.');
        } catch (error) {
            console.error('✗ Error loading JSON:', error);
            alert('Kon JSON niet laden: ' + error.message);
        }
    },

    populateFormFromData(data) {
        if (!data || !Array.isArray(data.members)) {
            throw new Error('Ongeldig JSON-formaat: members ontbreekt.');
        }

        const householdId = data.household_id || 'WEB_001';
        const strategy = data.allocation_strategy || 'EQUAL';
        const members = data.members;

        document.getElementById('householdId').value = householdId;
        this.allocationStrategy.value = strategy;

        const memberCount = Math.max(1, members.length);
        this.memberCount.value = String(memberCount);
        this.renderMembers(memberCount);

        members.forEach((member, index) => {
            const i = index + 1;

            const fullNameEl = document.getElementById(`fullName-${i}`);
            const bsnEl = document.getElementById(`bsn-${i}`);
            const residencyEl = document.getElementById(`residency-${i}`);
            const withheldEl = document.getElementById(`withheld-${i}`);
            const dividendTaxEl = document.getElementById(`dividend-tax-${i}`);
            const ownHomeEnabledEl = document.getElementById(`own-home-enabled-${i}`);
            const ownHomeWozEl = document.getElementById(`own-home-woz-${i}`);
            const ownHomePeriodEl = document.getElementById(`own-home-period-${i}`);

            if (fullNameEl) fullNameEl.value = member.full_name || '';
            if (bsnEl) bsnEl.value = member.bsn || '';
            if (residencyEl) residencyEl.value = member.residency_status || 'RESIDENT';
            if (withheldEl) withheldEl.value = member.withheld_tax || 0;
            if (dividendTaxEl) dividendTaxEl.value = member.dividend_tax_paid || 0;

            const hasOwnHome = !!member.own_home;
            if (ownHomeEnabledEl) ownHomeEnabledEl.checked = hasOwnHome;
            if (ownHomeWozEl) ownHomeWozEl.value = hasOwnHome ? (member.own_home.woz_value || '') : '';
            if (ownHomePeriodEl) ownHomePeriodEl.value = hasOwnHome ? (member.own_home.period_fraction || 1) : 1;

            if (Array.isArray(member.incomes)) {
                member.incomes.forEach((income) => {
                    this.addIncome(i);
                    const incomeRows = document.querySelectorAll(`#incomes-${i} .item-row`);
                    const row = incomeRows[incomeRows.length - 1];
                    row.querySelector('[data-type="income-type"]').value = income.type || 'EMPLOYMENT';
                    row.querySelector('[data-type="income-amount"]').value = income.amount || '';
                });
            }

            if (Array.isArray(member.deductions)) {
                member.deductions.forEach((deduction) => {
                    this.addDeduction(i);
                    const deductionRows = document.querySelectorAll(`#deductions-${i} .item-row`);
                    const row = deductionRows[deductionRows.length - 1];
                    row.querySelector('[data-type="deduction-desc"]').value = deduction.description || '';
                    row.querySelector('[data-type="deduction-amount"]').value = deduction.amount || '';
                });
            }

            if (Array.isArray(member.assets)) {
                member.assets.forEach((asset) => {
                    this.addAsset(i);
                    const assetRows = document.querySelectorAll(`#assets-${i} .item-row`);
                    const row = assetRows[assetRows.length - 1];
                    row.querySelector('[data-type="asset-type"]').value = asset.type || 'SAVINGS';
                    row.querySelector('[data-type="asset-value"]').value = asset.value || '';
                });
            }

            if (Array.isArray(member.tax_credits)) {
                member.tax_credits.forEach((credit) => {
                    this.addTaxCredit(i);
                    const creditRows = document.querySelectorAll(`#tax-credits-${i} .item-row`);
                    const row = creditRows[creditRows.length - 1];
                    row.querySelector('[data-type="credit-name"]').value = credit.name || '';
                    row.querySelector('[data-type="credit-amount"]').value = credit.amount || '';
                });
            }
        });
    },

    // Render member sections
    renderMembers(count) {
        this.currentMemberCount = count;
        this.membersContainer.innerHTML = '';

        for (let i = 1; i <= count; i++) {
            this.membersContainer.appendChild(this.createMemberCard(i));
        }
    },

    // Create member card HTML
    createMemberCard(memberNumber) {
        const card = document.createElement('div');
        card.className = `member-card member-${memberNumber}`;
        card.id = `member-${memberNumber}`;

        card.innerHTML = `
            <div class="member-card-header">
                <span class="member-card-title">👤 Persoon ${memberNumber}</span>
                ${this.currentMemberCount > 1 ? `<button type="button" class="remove-member-btn" onclick="app.removeMember(${memberNumber})">Verwijderen</button>` : ''}
            </div>

            <!-- Basic Info -->
            <div class="mb-3">
                  <label for="fullName-${memberNumber}" class="form-label">Volledige naam *</label>
                <input type="text" class="form-control" id="fullName-${memberNumber}" 
                      placeholder="bijv. Jan Jansen" required>
            </div>

            <div class="mb-3">
                <label for="bsn-${memberNumber}" class="form-label">BSN</label>
                <input type="text" class="form-control" id="bsn-${memberNumber}" 
                       placeholder="9 digits" maxlength="9">
            </div>

            <div class="mb-3">
                <label for="residency-${memberNumber}" class="form-label">Fiscale woonstatus</label>
                <select class="form-select" id="residency-${memberNumber}">
                    <option value="RESIDENT" selected>Ingezetene (heffingskortingen van toepassing)</option>
                    <option value="NON_RESIDENT">Niet-ingezetene</option>
                </select>
            </div>

            <!-- Income Sources -->
            <div class="subsection">
                <label class="subsection-label">💰 Inkomstenbronnen</label>
                <div id="incomes-${memberNumber}" class="income-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addIncome(${memberNumber})">
                    + Inkomstenbron toevoegen
                </button>
            </div>

            <!-- Deductions -->
            <div class="subsection">
                <label class="subsection-label">📝 Aftrekposten</label>
                <div id="deductions-${memberNumber}" class="deduction-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addDeduction(${memberNumber})">
                    + Aftrekpost toevoegen
                </button>
            </div>

            <!-- Tax Credits -->
            <div class="subsection">
                <label class="subsection-label">🎯 Heffingskortingen</label>
                <div id="tax-credits-${memberNumber}" class="tax-credit-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addTaxCredit(${memberNumber})">
                    + Add Heffingskorting
                </button>
            </div>

            <!-- Own Home -->
            <div class="subsection">
                <label class="subsection-label">🏠 Eigen Woning (Eigenwoningforfait)</label>
                <div class="row g-2">
                    <div class="col-12">
                        <div class="form-check mt-1">
                            <input class="form-check-input" type="checkbox" id="own-home-enabled-${memberNumber}">
                            <label class="form-check-label" for="own-home-enabled-${memberNumber}">
                                Deze persoon heeft een eigen woning
                            </label>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <input type="number" class="form-control" id="own-home-woz-${memberNumber}" placeholder="WOZ-waarde (€)" min="0" step="0.01">
                    </div>
                    <div class="col-md-5">
                        <input type="number" class="form-control" id="own-home-period-${memberNumber}" placeholder="Periode (0-1)" min="0" max="1" step="0.01" value="1">
                    </div>
                </div>
            </div>

            <!-- Prepaid Taxes -->
            <div class="subsection">
                <label for="withheld-${memberNumber}" class="form-label">Ingehouden Loonheffing (€)</label>
                <input type="number" class="form-control" id="withheld-${memberNumber}" placeholder="0.00" min="0" step="0.01" value="0">
                <label for="dividend-tax-${memberNumber}" class="form-label mt-2">Betaalde Dividendbelasting (€)</label>
                <input type="number" class="form-control" id="dividend-tax-${memberNumber}" placeholder="0.00" min="0" step="0.01" value="0">
            </div>

            <!-- Assets -->
            <div class="subsection">
                <label class="subsection-label">🏦 Vermogen (Box3)</label>
                <div id="assets-${memberNumber}" class="asset-list"></div>
                <button type="button" class="add-item-btn" onclick="app.addAsset(${memberNumber})">
                    + Vermogen toevoegen
                </button>
            </div>
        `;

        return card;
    },

    // Add income source input
    addIncome(memberNumber) {
        const incomeList = document.getElementById(`incomes-${memberNumber}`);
        const id = `income-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        let optionsHtml = this.incomeTypes.map(type => 
            `<option value="${type.id}">${type.label}</option>`
        ).join('');

        row.innerHTML = `
            <select class="form-select" data-type="income-type">
                ${optionsHtml}
            </select>
            <input type="number" class="form-control" placeholder="Bedrag (€)" min="0" step="0.01" data-type="income-amount" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Verwijderen</button>
        `;

        incomeList.appendChild(row);
    },

    // Add deduction input
    addDeduction(memberNumber) {
        const deductionList = document.getElementById(`deductions-${memberNumber}`);
        const id = `deduction-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        row.innerHTML = `
            <input type="text" class="form-control" placeholder="Omschrijving" data-type="deduction-desc" required>
            <input type="number" class="form-control" placeholder="Bedrag (€)" min="0" step="0.01" data-type="deduction-amount" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Verwijderen</button>
        `;

        deductionList.appendChild(row);
    },

    // Add tax credit input
    addTaxCredit(memberNumber) {
        const creditList = document.getElementById(`tax-credits-${memberNumber}`);
        const id = `tax-credit-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        row.innerHTML = `
            <input type="text" class="form-control" placeholder="Naam (bijv. Arbeidskorting)" data-type="credit-name" required>
            <input type="number" class="form-control" placeholder="Bedrag (€)" min="0" step="0.01" data-type="credit-amount" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Verwijderen</button>
        `;

        creditList.appendChild(row);
    },

    // Add asset input
    addAsset(memberNumber) {
        const assetList = document.getElementById(`assets-${memberNumber}`);
        const id = `asset-${memberNumber}-${Date.now()}`;

        const row = document.createElement('div');
        row.className = 'item-row two-col';
        row.id = id;

        let optionsHtml = this.assetTypes.map(type => 
            `<option value="${type.id}">${type.label}</option>`
        ).join('');

        row.innerHTML = `
            <select class="form-select" data-type="asset-type">
                ${optionsHtml}
            </select>
            <input type="number" class="form-control" placeholder="Waarde (€)" min="0" step="0.01" data-type="asset-value" required>
            <button type="button" class="remove-item-btn" onclick="app.removeItem('${id}')">Verwijderen</button>
        `;

        assetList.appendChild(row);
    },

    // Remove item from list
    removeItem(id) {
        document.getElementById(id).remove();
    },

    // Remove member
    removeMember(memberNumber) {
        document.getElementById(`member-${memberNumber}`).remove();
        this.memberCount.value = this.currentMemberCount - 1;
        this.currentMemberCount--;
    },

    // Collect form data
    collectFormData() {
        const householdId = document.getElementById('householdId').value || 'WEB_001';
        const allocationStrategy = document.getElementById('allocationStrategy').value;
        const members = [];

        for (let i = 1; i <= this.currentMemberCount; i++) {
            const memberCard = document.getElementById(`member-${i}`);
            if (!memberCard) continue;

            const member = {
                full_name: document.getElementById(`fullName-${i}`).value,
                bsn: document.getElementById(`bsn-${i}`).value || '',
                residency_status: document.getElementById(`residency-${i}`).value,
                incomes: [],
                deductions: [],
                withheld_tax: parseFloat(document.getElementById(`withheld-${i}`).value) || 0,
                dividend_tax_paid: parseFloat(document.getElementById(`dividend-tax-${i}`).value) || 0,
                tax_credits: [],
                assets: []
            };

            const ownHomeEnabled = document.getElementById(`own-home-enabled-${i}`).checked;
            const ownHomeWoz = parseFloat(document.getElementById(`own-home-woz-${i}`).value);
            const ownHomePeriod = parseFloat(document.getElementById(`own-home-period-${i}`).value);
            if (ownHomeEnabled && !Number.isNaN(ownHomeWoz) && ownHomeWoz > 0) {
                member.own_home = {
                    woz_value: ownHomeWoz,
                    period_fraction: Number.isNaN(ownHomePeriod) ? 1 : ownHomePeriod
                };
            }

            // Collect incomes
            const incomeRows = memberCard.querySelectorAll('#incomes-' + i + ' .item-row');
            incomeRows.forEach(row => {
                const type = row.querySelector('[data-type="income-type"]').value;
                const amount = row.querySelector('[data-type="income-amount"]').value;
                if (amount) {
                    member.incomes.push({
                        type: type,
                        amount: parseFloat(amount),
                        description: type
                    });
                }
            });

            // Collect deductions
            const deductionRows = memberCard.querySelectorAll('#deductions-' + i + ' .item-row');
            deductionRows.forEach(row => {
                const desc = row.querySelector('[data-type="deduction-desc"]').value;
                const amount = row.querySelector('[data-type="deduction-amount"]').value;
                if (desc && amount) {
                    member.deductions.push({
                        description: desc,
                        amount: parseFloat(amount)
                    });
                }
            });

            // Collect assets
            const assetRows = memberCard.querySelectorAll('#assets-' + i + ' .item-row');
            assetRows.forEach(row => {
                const type = row.querySelector('[data-type="asset-type"]').value;
                const value = row.querySelector('[data-type="asset-value"]').value;
                if (value) {
                    member.assets.push({
                        type: type,
                        value: parseFloat(value),
                        description: type
                    });
                }
            });

            // Collect tax credits/heffingskortingen
            const creditRows = memberCard.querySelectorAll('#tax-credits-' + i + ' .item-row');
            creditRows.forEach(row => {
                const name = row.querySelector('[data-type="credit-name"]').value;
                const amount = row.querySelector('[data-type="credit-amount"]').value;
                if (name && amount) {
                    member.tax_credits.push({
                        name: name,
                        amount: parseFloat(amount)
                    });
                }
            });

            members.push(member);
        }

        return {
            household_id: householdId,
            allocation_strategy: allocationStrategy,
            members: members
        };
    },

    // Calculate taxes
    async calculateTaxes() {
        try {
            this.loadingSpinner.classList.remove('d-none');

            const data = this.collectFormData();

            if (data.members.length === 0) {
                alert('Voeg minimaal een persoon met inkomsten toe.');
                this.loadingSpinner.classList.add('d-none');
                return;
            }

            console.log('Sending calculation request:', data);

            const response = await fetch(this.API_CALCULATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            console.log('Response status:', response.status);

            const result = await response.json();

            console.log('Calculation result:', result);

            if (result.error) {
                console.error('API Error:', result.error);
                alert('Fout: ' + result.error);
            } else if (result.success) {
                console.log('✓ Calculation successful');
                this.displayResults(result);
            } else {
                console.error('Unexpected response:', result);
                alert('De berekening gaf geen verwacht antwoordformaat terug.');
            }
        } catch (error) {
            console.error('✗ Error calculating taxes:', error);
            alert('Fout bij belastingberekening: ' + error.message);
        } finally {
            this.loadingSpinner.classList.add('d-none');
        }
    },

    // Display results
    displayResults(result) {
        console.log('Displaying results:', result);
        
        // Show results, hide empty state
        this.resultsSection.style.display = 'block';
        this.emptyState.style.display = 'none';

        // Update summary cards
        document.getElementById('totalTaxAmount').textContent = this.formatCurrency(result.net_settlement);
        document.getElementById('effectiveRateAmount').textContent = result.effective_tax_rate.toFixed(2) + '%';

        // Update Box1
        let box1Html = '';
        for (const [name, details] of Object.entries(result.box1_breakdown)) {
            box1Html += `
                <div class="member-detail">
                    <div class="member-detail-name">${name}</div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Bruto inkomen:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.gross_income)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Aftrekposten:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.deductions)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Belastbaar inkomen:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.taxable_income)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Box1 belasting:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.box1_tax)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Ingehouden loonheffing:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.withheld_tax)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Betaalde dividendbelasting:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.dividend_tax_paid || 0)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Voorheffingen totaal:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.prepaid_taxes || 0)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label">Heffingskortingen:</span>
                        <span class="member-detail-value">${this.formatCurrency(details.tax_credits)}</span>
                    </div>
                    <div class="member-detail-row">
                        <span class="member-detail-label"><strong>Netto last:</strong></span>
                        <span class="member-detail-value"><strong>${this.formatCurrency(details.net_liability)}</strong></span>
                    </div>
                </div>
            `;
        }
        document.getElementById('box1Details').innerHTML = box1Html;
        document.getElementById('box1Total').textContent = this.formatCurrency(result.box1_total);

        // Update Box3
        document.getElementById('totalAssets').textContent = this.formatCurrency(result.total_assets);
        document.getElementById('box3Rate').textContent = result.box3_rate.toFixed(2) + '%';

        let allocationHtml = '';
        for (const [name, amount] of Object.entries(result.box3_allocation)) {
            allocationHtml += `
                <div class="member-detail-row">
                    <span class="member-detail-label">${name}:</span>
                    <span class="member-detail-value">${this.formatCurrency(amount)}</span>
                </div>
            `;
        }
        document.getElementById('box3Allocation').innerHTML = allocationHtml;
        document.getElementById('box3Total').textContent = this.formatCurrency(result.box3_tax);

        // Update process flow details
        document.getElementById('box1TaxableIncomeTotal').textContent = this.formatCurrency(result.box1_taxable_income_total);
        document.getElementById('box3DeemedReturn').textContent = this.formatCurrency(result.box3_deemed_return);
        document.getElementById('box3TaxFreeAssets').textContent = this.formatCurrency(result.box3_tax_free_assets);
        document.getElementById('box3CorrectedDeemedReturn').textContent = this.formatCurrency(result.box3_corrected_deemed_return);
        document.getElementById('verzamelinkomen').textContent = this.formatCurrency(result.verzamelinkomen);
        document.getElementById('grossIncomeTax').textContent = this.formatCurrency(result.gross_income_tax);
        document.getElementById('totalPrepaidTaxes').textContent = this.formatCurrency(result.total_prepaid_taxes);
        document.getElementById('totalTaxCredits').textContent = this.formatCurrency(result.total_tax_credits);
        document.getElementById('netSettlement').textContent = this.formatCurrency(result.net_settlement);

        // Update final total
        document.getElementById('finalTotalTax').textContent = this.formatCurrency(result.net_settlement);
    },

    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('nl-NL', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    },

    // Clear results
    clearResults() {
        this.resultsSection.style.display = 'none';
        this.emptyState.style.display = 'block';
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
