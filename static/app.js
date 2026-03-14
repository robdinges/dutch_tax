const app = {
    API_CALCULATE: "/api/calculate",
    API_JOINT_PREVIEW: "/api/joint-items-preview",
    currentMemberCount: 2,
    BOX3_SAVINGS_RATE: 0.0137,
    BOX3_INVESTMENTS_RATE: 0.0588,
    JOINT_ITEMS: [
        { key: "eigenwoningforfait", label: "Eigenwoningforfait (bijtelling Box 1)" },
        { key: "aftrek_geen_of_kleine_eigenwoningschuld", label: "Aftrek geen of kleine eigenwoningschuld (76,667%)" },
        { key: "grondslag_voordeel_sparen_beleggen", label: "Grondslag voordeel uit sparen en beleggen" },
        { key: "vrijstelling_groene_beleggingen", label: "Vrijstelling groene beleggingen" },
        { key: "ingehouden_dividendbelasting", label: "Ingehouden dividendbelasting" },
        { key: "ingehouden_buitenlandse_dividendbelasting", label: "Ingehouden buitenlandse dividendbelasting" },
    ],
    latestJointPreview: null,
    distributionConfirmed: false,
    distributionRefreshTimer: null,

    init() {
        this.cacheElements();
        this.attachEvents();
        this.renderMembers(this.currentMemberCount);
        this.renderCreditsPerPerson(this.currentMemberCount);
        this.initBox3HouseholdEditors();
        this.scheduleJointDistributionRefresh();
    },

    cacheElements() {
        this.form = document.getElementById("taxForm");
        this.memberCount = document.getElementById("memberCount");
        this.membersContainer = document.getElementById("membersContainer");
        this.creditsContainer = document.getElementById("creditsContainer");
        this.resultsSection = document.getElementById("resultsSection");
        this.emptyState = document.getElementById("emptyState");
        this.loadJsonFile = document.getElementById("loadJsonFile");
        this.loadJsonBtn = document.getElementById("loadJsonBtn");
        this.jointDistributionContainer = document.getElementById("jointDistributionContainer");
        this.confirmDistributionBtn = document.getElementById("confirmDistributionBtn");
        this.distributionStatus = document.getElementById("distributionStatus");

        this.savingsList = document.getElementById("savings-list");
        this.investmentsList = document.getElementById("investments-list");
        this.otherAssetsList = document.getElementById("other-assets-list");
        this.debtsList = document.getElementById("debts-list");
        this.addSavingsBtn = document.getElementById("addSavingsBtn");
        this.addInvestmentsBtn = document.getElementById("addInvestmentsBtn");
        this.addOtherAssetBtn = document.getElementById("addOtherAssetBtn");
        this.addDebtBtn = document.getElementById("addDebtBtn");
    },

    attachEvents() {
        this.memberCount.addEventListener("change", (event) => {
            this.currentMemberCount = Number(event.target.value);
            this.renderMembers(this.currentMemberCount);
            this.renderCreditsPerPerson(this.currentMemberCount);
            this.markDistributionStale();
            this.scheduleJointDistributionRefresh();
        });

        this.form.addEventListener("submit", async (event) => {
            event.preventDefault();
            await this.calculate();
        });

        this.loadJsonBtn.addEventListener("click", () => {
            this.loadJsonIntoForm();
        });

        this.confirmDistributionBtn.addEventListener("click", async () => {
            await this.confirmJointDistribution();
        });

        this.form.addEventListener("input", (event) => {
            if (event.target?.dataset?.jointDistributionInput === "1") {
                this.updateDistributionValidationStatus();
                return;
            }
            this.markDistributionStale();
            this.scheduleJointDistributionRefresh();
        });

        this.addSavingsBtn.addEventListener("click", () => this.addSavingsRow());
        this.addInvestmentsBtn.addEventListener("click", () => this.addInvestmentRow());
        this.addOtherAssetBtn.addEventListener("click", () => this.addOtherAssetRow());
        this.addDebtBtn.addEventListener("click", () => this.addDebtRow());
    },

    initBox3HouseholdEditors() {
        this.savingsList.innerHTML = "";
        this.investmentsList.innerHTML = "";
        this.otherAssetsList.innerHTML = "";
        this.debtsList.innerHTML = "";
        this.addSavingsRow();
        this.addInvestmentRow();
        this.addOtherAssetRow();
        this.addDebtRow();
        this.updateBox3Subtotals();
    },

    renderMembers(count) {
        this.membersContainer.innerHTML = "";
        for (let i = 1; i <= count; i += 1) {
            this.membersContainer.appendChild(this.createMemberCard(i));
        }
    },

    renderCreditsPerPerson(count) {
        this.creditsContainer.innerHTML = "";
        for (let i = 1; i <= count; i += 1) {
            const node = document.createElement("article");
            node.className = "member-card";
            node.id = `credits-member-${i}`;
            node.innerHTML = `
                <header><h4>Persoon ${i} - Heffingskortingen</h4></header>
                <div class="editor-header simple-header">
                    <span>Naam</span>
                    <span>Bedrag</span>
                    <span>Actie</span>
                </div>
                <div id="credits-list-${i}"></div>
                <button type="button" class="btn ghost" onclick="app.addCreditRow(${i})">+ Heffingskorting</button>
            `;
            this.creditsContainer.appendChild(node);
            this.addCreditRow(i);
        }
    },

    createMemberCard(index) {
        const node = document.createElement("article");
        node.className = "member-card";
        node.id = `member-${index}`;
        node.innerHTML = `
            <header>
                <h4>Persoon ${index}</h4>
            </header>

            <div class="grid two">
                <label>Naam
                    <input type="text" id="full-name-${index}" value="Persoon ${index}">
                </label>
                <label>BSN
                    <input type="text" id="bsn-${index}" value="00000000${index}">
                </label>
            </div>

            <section class="subblock">
                <h5>Box 1 - Inkomsten (1-4)</h5>
                <div class="grid two">
                    <label class="inline-toggle">Ontvangt al AOW
                        <input type="checkbox" id="has-aow-${index}">
                    </label>
                </div>
                <div class="editor-header income-header">
                    <span>Soort</span>
                    <span>Instantie/bedrijf/werkgever</span>
                    <span>Bedrag</span>
                    <span>Arbeidskorting</span>
                    <span>Loonheffing</span>
                    <span>Actie</span>
                </div>
                <div id="incomes-list-${index}"></div>
                <button type="button" class="btn ghost" onclick="app.addIncomeRow(${index})">+ Inkomensregel</button>
            </section>

            <section class="subblock">
                <h5>Persoonsgebonden aftrekposten (8-13)</h5>
                <div class="editor-header simple-header">
                    <span>Omschrijving</span>
                    <span>Bedrag</span>
                    <span>Actie</span>
                </div>
                <div id="deductions-list-${index}"></div>
                <button type="button" class="btn ghost" onclick="app.addDeductionRow(${index})">+ Persoonsgebonden aftrekpost</button>
            </section>

            <section class="subblock">
                <h5>Box 2 - Aanmerkelijk belang</h5>
                <div class="grid two">
                    <label class="inline-toggle">5% of meer belang in BV
                        <input type="checkbox" id="has-ab-${index}">
                    </label>
                    <label>Dividend
                        <input type="number" min="0" step="1" id="box2-dividend-${index}" value="0">
                    </label>
                    <label>Verkoopopbrengst/winst aandelen
                        <input type="number" min="0" step="1" id="box2-sale-${index}" value="0">
                    </label>
                    <label>Verkrijgingsprijs
                        <input type="number" min="0" step="1" id="box2-acquisition-${index}" value="0">
                    </label>
                </div>
            </section>
        `;
        setTimeout(() => {
            this.addIncomeRow(index);
            this.addDeductionRow(index);
        }, 0);
        return node;
    },

    makeRowId(prefix) {
        return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 9999)}`;
    },

    addSavingsRow(name = "", amount = 0, isGreen = false) {
        const rowId = this.makeRowId("savings-row");
        const node = document.createElement("div");
        node.className = "editor-row savings-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Spaarrekening
                <input type="text" data-kind="name" maxlength="40" value="${name}">
            </label>
            <label>Saldo
                <input type="number" min="0" step="1" data-kind="amount" value="${amount}">
            </label>
            <label class="inline-toggle">Groen sparen
                <input type="checkbox" data-kind="is-green" ${isGreen ? "checked" : ""}>
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        this.savingsList.appendChild(node);
        this.attachBox3RowListeners(node);
    },

    addInvestmentRow(name = "", amount = 0, isGreen = false, dividendWithholding = 0, foreignDividendWithholding = 0) {
        const rowId = this.makeRowId("invest-row");
        const node = document.createElement("div");
        node.className = "editor-row investments-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Beleggingsrekening
                <input type="text" data-kind="name" maxlength="40" value="${name}">
            </label>
            <label>Waarde
                <input type="number" min="0" step="1" data-kind="amount" value="${amount}">
            </label>
            <label class="inline-toggle">Groene belegging
                <input type="checkbox" data-kind="is-green" ${isGreen ? "checked" : ""}>
            </label>
            <label>Dividendbelasting
                <input type="number" min="0" step="1" data-kind="dividend-withholding" value="${dividendWithholding}">
            </label>
            <label>Buitenlandse dividendbelasting
                <input type="number" min="0" step="1" data-kind="foreign-dividend-withholding" value="${foreignDividendWithholding}">
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        this.investmentsList.appendChild(node);
        this.attachBox3RowListeners(node);
    },

    addOtherAssetRow(name = "", amount = 0) {
        const rowId = this.makeRowId("other-asset-row");
        const node = document.createElement("div");
        node.className = "editor-row simple-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Omschrijving
                <input type="text" data-kind="name" maxlength="50" value="${name}">
            </label>
            <label>Bedrag
                <input type="number" min="0" step="1" data-kind="amount" value="${amount}">
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        this.otherAssetsList.appendChild(node);
        this.attachBox3RowListeners(node);
    },

    addDebtRow(name = "", amount = 0) {
        const rowId = this.makeRowId("debt-row");
        const node = document.createElement("div");
        node.className = "editor-row simple-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Omschrijving
                <input type="text" data-kind="name" maxlength="50" value="${name}">
            </label>
            <label>Bedrag
                <input type="number" min="0" step="1" data-kind="amount" value="${amount}">
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        this.debtsList.appendChild(node);
        this.attachBox3RowListeners(node);
    },

    attachBox3RowListeners(node) {
        node.querySelectorAll("input").forEach((input) => {
            input.addEventListener("input", () => this.updateBox3Subtotals());
            input.addEventListener("change", () => this.updateBox3Subtotals());
        });
        this.updateBox3Subtotals();
    },

    updateBox3Subtotals() {
        const sumBySelector = (selector, amountKind = "amount", excludeGreen = false) => {
            const rows = document.querySelectorAll(selector);
            let sum = 0;
            rows.forEach((row) => {
                const isGreen = Boolean(row.querySelector("[data-kind='is-green']")?.checked);
                if (excludeGreen && isGreen) {
                    return;
                }
                sum += Number(row.querySelector(`[data-kind='${amountKind}']`)?.value || 0);
            });
            return sum;
        };

        const savings = sumBySelector("#savings-list > div", "amount", true);
        const investments = sumBySelector("#investments-list > div", "amount", true);
        const otherAssets = sumBySelector("#other-assets-list > div");
        const debts = sumBySelector("#debts-list > div");

        document.getElementById("subtotalSavings").textContent = this.currency(savings);
        document.getElementById("subtotalInvestments").textContent = this.currency(investments);
        document.getElementById("subtotalOtherAssets").textContent = this.currency(otherAssets);
        document.getElementById("subtotalDebts").textContent = this.currency(-debts);

        document.getElementById("deemedSavings").textContent = this.currency(savings * this.BOX3_SAVINGS_RATE);
        document.getElementById("deemedInvestments").textContent = this.currency(investments * this.BOX3_INVESTMENTS_RATE);
    },

    addIncomeRow(index, type = "EMPLOYMENT", source = "", amount = 0, laborCredit = 0, wageWithholding = 0) {
        const container = document.getElementById(`incomes-list-${index}`);
        const rowId = this.makeRowId(`income-row-${index}`);
        const node = document.createElement("div");
        node.className = "editor-row income-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Soort inkomen
                <select data-kind="income-type">
                    <option value="EMPLOYMENT" ${type === "EMPLOYMENT" ? "selected" : ""}>Loon</option>
                    <option value="SELF_EMPLOYMENT" ${type === "SELF_EMPLOYMENT" ? "selected" : ""}>Winst onderneming</option>
                    <option value="BENEFITS" ${type === "BENEFITS" ? "selected" : ""}>Uitkeringen</option>
                    <option value="PENSION" ${type === "PENSION" ? "selected" : ""}>Pensioen</option>
                </select>
            </label>
            <label>Instantie/bedrijf/werkgever
                <input type="text" data-kind="income-source" maxlength="60" value="${source}">
            </label>
            <label>Bedrag
                <input type="number" min="0" step="1" data-kind="income-amount" value="${amount}">
            </label>
            <label>Arbeidskorting
                <input type="number" min="0" step="1" data-kind="income-labor-credit" value="${laborCredit}">
            </label>
            <label>Loonheffing
                <input type="number" min="0" step="1" data-kind="income-withholding" value="${wageWithholding}">
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        container.appendChild(node);
    },

    addDeductionRow(index, name = "", amount = 0) {
        const container = document.getElementById(`deductions-list-${index}`);
        const rowId = this.makeRowId(`deduction-row-${index}`);
        const node = document.createElement("div");
        node.className = "editor-row simple-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Omschrijving aftrekpost
                <input type="text" data-kind="deduction-name" maxlength="60" value="${name}">
            </label>
            <label>Bedrag
                <input type="number" min="0" step="1" data-kind="deduction-amount" value="${amount}">
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        container.appendChild(node);
    },

    addCreditRow(index, name = "", amount = 0) {
        const container = document.getElementById(`credits-list-${index}`);
        const rowId = this.makeRowId(`credit-row-${index}`);
        const node = document.createElement("div");
        node.className = "editor-row simple-row";
        node.id = rowId;
        node.innerHTML = `
            <label>Naam heffingskorting
                <input type="text" data-kind="credit-name" maxlength="50" value="${name}">
            </label>
            <label>Bedrag
                <input type="number" min="0" step="1" data-kind="credit-amount" value="${amount}">
            </label>
            <button type="button" class="btn ghost row-remove" onclick="app.removeRow('${rowId}')">Verwijder</button>
        `;
        container.appendChild(node);
    },

    removeRow(id) {
        const row = document.getElementById(id);
        if (row) {
            row.remove();
            this.updateBox3Subtotals();
        }
    },

    readNumber(id) {
        const value = document.getElementById(id)?.value;
        return Number(value || 0);
    },

    markDistributionStale() {
        this.distributionConfirmed = false;
        if (this.distributionStatus) {
            this.distributionStatus.textContent = "Verdeling moet opnieuw worden bevestigd";
            this.distributionStatus.classList.remove("ok");
            this.distributionStatus.classList.add("warn");
        }
    },

    scheduleJointDistributionRefresh() {
        if (this.distributionRefreshTimer) {
            clearTimeout(this.distributionRefreshTimer);
        }
        this.distributionRefreshTimer = setTimeout(() => {
            this.refreshJointDistributionPreview();
        }, 250);
    },

    memberDirectory() {
        const directory = [];
        for (let i = 1; i <= this.currentMemberCount; i += 1) {
            const memberId = document.getElementById(`bsn-${i}`).value || `member_${i}`;
            const fullName = document.getElementById(`full-name-${i}`).value || `Persoon ${i}`;
            directory.push({ memberId, fullName });
        }
        return directory;
    },

    collectJointDistribution() {
        const distribution = {};
        this.JOINT_ITEMS.forEach((item) => {
            distribution[item.key] = {};
        });

        const inputs = this.jointDistributionContainer.querySelectorAll("[data-joint-distribution-input='1']");
        inputs.forEach((input) => {
            const itemKey = input.dataset.itemKey;
            const memberId = input.dataset.memberId;
            if (!itemKey || !memberId || !distribution[itemKey]) {
                return;
            }
            distribution[itemKey][memberId] = Number(input.value || 0);
        });

        return distribution;
    },

    currentPreviewPayload() {
        const payload = this.collectPayload();
        delete payload.joint_distribution;
        return payload;
    },

    async refreshJointDistributionPreview(prefillDistribution = null) {
        const payload = this.currentPreviewPayload();
        const response = await fetch(this.API_JOINT_PREVIEW, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok || result.error) {
            this.distributionStatus.textContent = result.error || "Kon gezamenlijke posten niet ophalen";
            this.distributionStatus.classList.remove("ok");
            this.distributionStatus.classList.add("warn");
            return;
        }

        this.latestJointPreview = result;
        this.renderJointDistribution(result, prefillDistribution);
        this.updateDistributionValidationStatus();
    },

    renderJointDistribution(preview, prefillDistribution = null) {
        const memberIds = preview.member_ids || [];
        const totals = preview.joint_distribution_totals || {};
        const memberLabels = preview.member_labels || {};
        const existing = this.collectJointDistribution();
        const source = prefillDistribution || existing;

        const memberHeader = memberIds.map((memberId) => `<th>${memberLabels[memberId] || memberId}</th>`).join("");
        const rows = this.JOINT_ITEMS.map((item) => {
            const total = Number(totals[item.key] || 0);
            const currentValues = memberIds.map((memberId) => {
                const explicit = source?.[item.key]?.[memberId];
                if (explicit !== undefined && explicit !== null) {
                    return Number(explicit);
                }
                return Number((total / Math.max(memberIds.length, 1)).toFixed(2));
            });

            const allocatedSoFar = currentValues.slice(0, -1).reduce((sum, value) => sum + Number(value || 0), 0);
            if (memberIds.length > 1 && (source?.[item.key]?.[memberIds[memberIds.length - 1]] === undefined)) {
                currentValues[currentValues.length - 1] = Number((total - allocatedSoFar).toFixed(2));
            }

            const memberCells = memberIds.map((memberId, index) => {
                const value = Number(currentValues[index] || 0);
                return `
                    <td>
                        <input
                            type="number"
                            min="0"
                            step="0.01"
                            value="${value}"
                            data-joint-distribution-input="1"
                            data-item-key="${item.key}"
                            data-member-id="${memberId}"
                        >
                    </td>
                `;
            }).join("");

            return `
                <tr data-item-row="${item.key}">
                    <td>${item.label}</td>
                    <td class="mono">${this.currency(total)}</td>
                    ${memberCells}
                    <td class="distribution-check" data-check-key="${item.key}">-</td>
                </tr>
            `;
        }).join("");

        this.jointDistributionContainer.innerHTML = `
            <div class="distribution-wrap">
                <table class="distribution-table">
                    <thead>
                        <tr>
                            <th>Post</th>
                            <th>Totaal</th>
                            ${memberHeader}
                            <th>Controle</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    },

    validateJointDistributionTotals() {
        const totals = this.latestJointPreview?.joint_distribution_totals || {};
        const distribution = this.collectJointDistribution();
        const memberIds = this.latestJointPreview?.member_ids || [];
        const rowStates = {};
        let isValid = true;

        this.JOINT_ITEMS.forEach((item) => {
            const total = Number(totals[item.key] || 0);
            const sum = memberIds.reduce((acc, memberId) => {
                return acc + Number(distribution?.[item.key]?.[memberId] || 0);
            }, 0);
            const diff = Math.abs(total - sum);
            const rowValid = diff <= 0.01;
            rowStates[item.key] = { total, sum, rowValid };
            if (!rowValid) {
                isValid = false;
            }
        });

        return { isValid, rowStates };
    },

    updateDistributionValidationStatus() {
        const validation = this.validateJointDistributionTotals();
        Object.entries(validation.rowStates).forEach(([itemKey, state]) => {
            const cell = this.jointDistributionContainer.querySelector(`[data-check-key='${itemKey}']`);
            if (!cell) {
                return;
            }
            if (state.rowValid) {
                cell.textContent = "OK";
                cell.classList.remove("bad");
                cell.classList.add("good");
            } else {
                cell.textContent = `${this.currency(state.sum)} i.p.v. ${this.currency(state.total)}`;
                cell.classList.remove("good");
                cell.classList.add("bad");
            }
        });
        return validation.isValid;
    },

    async confirmJointDistribution() {
        await this.refreshJointDistributionPreview();
        const isValid = this.updateDistributionValidationStatus();
        if (!isValid) {
            this.distributionConfirmed = false;
            this.distributionStatus.textContent = "Verdeling ongeldig: controleer de regels met afwijking.";
            this.distributionStatus.classList.remove("ok");
            this.distributionStatus.classList.add("warn");
            return;
        }

        this.distributionConfirmed = true;
        this.distributionStatus.textContent = "Verdeling bevestigd. Je kunt doorgaan naar de volgende stap.";
        this.distributionStatus.classList.remove("warn");
        this.distributionStatus.classList.add("ok");

        const nextStep = this.creditsContainer?.closest("section");
        if (nextStep) {
            nextStep.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    },

    collectBox3Household() {
        const collect = (selector) => {
            const rows = document.querySelectorAll(selector);
            return Array.from(rows);
        };

        const savingsAccounts = collect("#savings-list > div").map((row) => ({
            name: row.querySelector("[data-kind='name']")?.value || "Spaarrekening",
            amount: Number(row.querySelector("[data-kind='amount']")?.value || 0),
            is_green: Boolean(row.querySelector("[data-kind='is-green']")?.checked),
        })).filter((x) => x.name || Math.abs(x.amount) > 0);

        const investmentAccounts = collect("#investments-list > div").map((row) => ({
            name: row.querySelector("[data-kind='name']")?.value || "Beleggingsrekening",
            amount: Number(row.querySelector("[data-kind='amount']")?.value || 0),
            is_green: Boolean(row.querySelector("[data-kind='is-green']")?.checked),
            dividend_withholding: Number(row.querySelector("[data-kind='dividend-withholding']")?.value || 0),
            foreign_dividend_withholding: Number(row.querySelector("[data-kind='foreign-dividend-withholding']")?.value || 0),
        })).filter((x) => x.name || x.amount > 0 || x.dividend_withholding > 0 || x.foreign_dividend_withholding > 0);

        const otherAssets = collect("#other-assets-list > div").map((row) => ({
            name: row.querySelector("[data-kind='name']")?.value || "Overige bezitting",
            amount: Number(row.querySelector("[data-kind='amount']")?.value || 0),
        })).filter((x) => x.name || x.amount > 0);

        const debts = collect("#debts-list > div").map((row) => ({
            name: row.querySelector("[data-kind='name']")?.value || "Schuld",
            amount: -Math.abs(Number(row.querySelector("[data-kind='amount']")?.value || 0)),
        })).filter((x) => x.name || x.amount > 0);

        const totalSavings = savingsAccounts
            .filter((item) => !item.is_green)
            .reduce((sum, item) => sum + item.amount, 0);
        const totalInvestments = investmentAccounts
            .filter((item) => !item.is_green)
            .reduce((sum, item) => sum + item.amount, 0);
        const totalOtherAssets = otherAssets.reduce((sum, item) => sum + item.amount, 0);
        const totalDebts = Math.abs(debts.reduce((sum, item) => sum + item.amount, 0));
        const totalDividendWithholding = investmentAccounts.reduce((sum, item) => sum + item.dividend_withholding, 0);
        const totalForeignDividendWithholding = investmentAccounts.reduce((sum, item) => sum + item.foreign_dividend_withholding, 0);

        return {
            savings_accounts: savingsAccounts,
            investment_accounts: investmentAccounts,
            other_assets_items: otherAssets,
            debt_items: debts,
            savings: totalSavings,
            investments: totalInvestments,
            other_assets: totalOtherAssets,
            debts: totalDebts,
            total_dividend_withholding: totalDividendWithholding,
            total_foreign_dividend_withholding: totalForeignDividendWithholding,
        };
    },

    collectPayload() {
        const members = [];

        for (let i = 1; i <= this.currentMemberCount; i += 1) {
            const bsn = document.getElementById(`bsn-${i}`).value || `member_${i}`;
            const memberId = bsn;

            const incomes = [];
            let wageWithholdingTotal = 0;
            const incomeRows = document.querySelectorAll(`#incomes-list-${i} > div`);
            incomeRows.forEach((row) => {
                const type = row.querySelector("[data-kind='income-type']")?.value || "EMPLOYMENT";
                const source = row.querySelector("[data-kind='income-source']")?.value || "";
                const amount = Number(row.querySelector("[data-kind='income-amount']")?.value || 0);
                const laborCredit = Number(row.querySelector("[data-kind='income-labor-credit']")?.value || 0);
                const wageWithholding = Number(row.querySelector("[data-kind='income-withholding']")?.value || 0);
                if (amount > 0) {
                    incomes.push({ type, amount, labor_credit: laborCredit, source, description: source || type });
                    wageWithholdingTotal += wageWithholding;
                }
            });

            const deductions = [];
            const deductionRows = document.querySelectorAll(`#deductions-list-${i} > div`);
            deductionRows.forEach((row) => {
                const name = row.querySelector("[data-kind='deduction-name']")?.value || "";
                const amount = Number(row.querySelector("[data-kind='deduction-amount']")?.value || 0);
                if (name && amount > 0) {
                    deductions.push({ type: "PERSONAL_ALLOWANCE", name, amount });
                }
            });

            const taxCredits = [];
            const creditRows = document.querySelectorAll(`#credits-list-${i} > div`);
            creditRows.forEach((row) => {
                const name = row.querySelector("[data-kind='credit-name']")?.value || "";
                const amount = Number(row.querySelector("[data-kind='credit-amount']")?.value || 0);
                if (name && amount > 0) {
                    taxCredits.push({ name, amount });
                }
            });

            members.push({
                member_id: memberId,
                full_name: document.getElementById(`full-name-${i}`).value || `Persoon ${i}`,
                bsn,
                wage_withholding: wageWithholdingTotal,
                box1: {
                    incomes,
                    deductions,
                    has_aow: document.getElementById(`has-aow-${i}`).checked,
                    tax_credits: taxCredits,
                },
                box2: {
                    has_substantial_interest: document.getElementById(`has-ab-${i}`).checked,
                    dividend_income: this.readNumber(`box2-dividend-${i}`),
                    sale_gain: this.readNumber(`box2-sale-${i}`),
                    acquisition_price: this.readNumber(`box2-acquisition-${i}`),
                },
            });
        }

        const box3Household = this.collectBox3Household();

        return {
            household_id: document.getElementById("householdId").value || "WEB_001",
            fiscal_partner: document.getElementById("fiscalPartner").checked,
            children_count: this.readNumber("childrenCount"),
            household_box1: {
                own_home: {
                    has_own_home: document.getElementById("has-own-home-household").checked,
                    woz_value: this.readNumber("woz-household"),
                    period_fraction: this.readNumber("period-household"),
                },
            },
            dividend_withholding_total: box3Household.total_dividend_withholding,
            foreign_dividend_withholding_total: box3Household.total_foreign_dividend_withholding,
            box3_household: box3Household,
            joint_distribution: this.collectJointDistribution(),
            members,
        };
    },

    async calculate() {
        if (!this.distributionConfirmed) {
            alert("Bevestig eerst de verdeling van gezamenlijke posten.");
            return;
        }

        if (!this.validateJointDistributionTotals().isValid) {
            alert("De verdeling is ongeldig. Zorg dat elke regel optelt tot het totaal.");
            return;
        }

        const payload = this.collectPayload();
        const response = await fetch(this.API_CALCULATE, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (!response.ok || result.error) {
            alert(result.error || "Berekening mislukt");
            return;
        }

        this.renderResults(result);
    },

    loadJsonIntoForm() {
        if (!this.loadJsonFile.files || this.loadJsonFile.files.length === 0) {
            alert("Selecteer eerst een JSON-bestand.");
            return;
        }

        const file = this.loadJsonFile.files[0];
        file.text().then(async (raw) => {
            const parsed = JSON.parse(raw);
            const payload = parsed.data || parsed;
            const members = payload.members || [];

            document.getElementById("householdId").value = payload.household_id || "WEB_001";
            document.getElementById("fiscalPartner").checked = Boolean(payload.fiscal_partner);
            document.getElementById("childrenCount").value = payload.children_count || 0;

            this.currentMemberCount = Math.max(1, members.length || 1);
            this.memberCount.value = String(this.currentMemberCount);
            this.renderMembers(this.currentMemberCount);
            this.renderCreditsPerPerson(this.currentMemberCount);

            members.forEach((member, idx) => {
                const i = idx + 1;
                document.getElementById(`full-name-${i}`).value = member.full_name || "";
                document.getElementById(`bsn-${i}`).value = member.bsn || "";

                const box1 = member.box1 || {};
                const incomes = box1.incomes || [];
                const incomeContainer = document.getElementById(`incomes-list-${i}`);
                incomeContainer.innerHTML = "";
                if (incomes.length === 0) {
                    this.addIncomeRow(i);
                } else {
                    const totalWithholding = Number(member.wage_withholding || 0);
                    const defaultPerRow = incomes.length > 0 ? totalWithholding / incomes.length : 0;
                    incomes.forEach((income) => {
                        this.addIncomeRow(
                            i,
                            income.type || "EMPLOYMENT",
                            income.source || income.description || "",
                            income.amount || 0,
                            income.labor_credit || 0,
                            defaultPerRow
                        );
                    });
                }

                const deductions = box1.deductions || [];
                const deductionContainer = document.getElementById(`deductions-list-${i}`);
                deductionContainer.innerHTML = "";
                if (deductions.length === 0) {
                    this.addDeductionRow(i);
                } else {
                    deductions.forEach((deduction) => {
                        this.addDeductionRow(i, deduction.name || deduction.type || "Aftrekpost", deduction.amount || 0);
                    });
                }

                document.getElementById(`has-aow-${i}`).checked = Boolean(box1.has_aow);

                const creditsContainer = document.getElementById(`credits-list-${i}`);
                creditsContainer.innerHTML = "";
                const credits = box1.tax_credits || [];
                if (credits.length === 0) {
                    this.addCreditRow(i);
                } else {
                    credits.forEach((credit) => {
                        this.addCreditRow(i, credit.name || "Heffingskorting", credit.amount || 0);
                    });
                }

                const box2 = member.box2 || {};
                document.getElementById(`has-ab-${i}`).checked = Boolean(box2.has_substantial_interest);
                document.getElementById(`box2-dividend-${i}`).value = box2.dividend_income || 0;
                document.getElementById(`box2-sale-${i}`).value = box2.sale_gain || 0;
                document.getElementById(`box2-acquisition-${i}`).value = box2.acquisition_price || 0;
            });

            const box3 = payload.box3_household || {};
            const householdBox1 = payload.household_box1 || {};
            const ownHome = householdBox1.own_home || payload.own_home || {};
            document.getElementById("has-own-home-household").checked = Boolean(ownHome.has_own_home);
            document.getElementById("woz-household").value = ownHome.woz_value || 0;
            document.getElementById("period-household").value = ownHome.period_fraction || 1;

            this.savingsList.innerHTML = "";
            (box3.savings_accounts || []).forEach((row) => this.addSavingsRow(row.name || "", row.amount || 0, !!row.is_green));
            if ((box3.savings_accounts || []).length === 0) {
                this.addSavingsRow("", box3.savings || 0, false);
            }

            this.investmentsList.innerHTML = "";
            (box3.investment_accounts || []).forEach((row) => this.addInvestmentRow(
                row.name || "",
                row.amount || row.value || 0,
                !!row.is_green,
                row.dividend_withholding || 0,
                row.foreign_dividend_withholding || 0,
            ));
            if ((box3.investment_accounts || []).length === 0) {
                this.addInvestmentRow(
                    "",
                    box3.investments || 0,
                    false,
                    payload.dividend_withholding_total || 0,
                    payload.foreign_dividend_withholding_total || 0,
                );
            }

            this.otherAssetsList.innerHTML = "";
            (box3.other_assets_items || []).forEach((row) => this.addOtherAssetRow(row.name || "", row.amount || 0));
            if ((box3.other_assets_items || []).length === 0) {
                this.addOtherAssetRow("", box3.other_assets || 0);
            }

            this.debtsList.innerHTML = "";
            (box3.debt_items || []).forEach((row) => this.addDebtRow(row.name || "", Math.abs(row.amount || 0)));
            if ((box3.debt_items || []).length === 0) {
                this.addDebtRow("", Math.abs(box3.debts || 0));
            }

            this.updateBox3Subtotals();
            this.markDistributionStale();
            await this.refreshJointDistributionPreview(payload.joint_distribution || {});
        }).catch((error) => {
            alert(`Kon JSON niet laden: ${error.message}`);
        });
    },

    renderResults(result) {
        this.resultsSection.classList.remove("hidden");
        this.emptyState.classList.add("hidden");

        const settlement = result.settlement;
        const box2 = result.box2;
        const box3 = result.box3;

        document.getElementById("kpiSettlement").textContent = this.currency(settlement.net_settlement);
        document.getElementById("kpiSettlementType").textContent = settlement.result_type;
        document.getElementById("kpiRate").textContent = `${settlement.effective_rate.toFixed(2)}%`;
        document.getElementById("kpiVerzamel").textContent = this.currency(result.verzamelinkomen);

        // Per-person sections following the belastingdienst structure
        const personsResults = result.members.map((member, index) => {
            const brackets = member.box1.brackets.map((row) => {
                return `<li>${row.description}: ${this.currency(row.tax_amount)} over ${this.currency(row.taxable_amount)}</li>`;
            }).join("");

            const creditItems = member.box1.credits.items.map((credit) => {
                return `<div class="totals-row"><span>${credit.name}</span><strong>-${this.currency(credit.amount)}</strong></div>`;
            }).join("");

            const grossTaxAndPremiums = Number(member.box1.tax || 0)
                + Number(member.box2.tax || 0)
                + Number(member.box3.tax || 0)
                + Number(member.premiums.total || 0);

            return `
                <section class="result-block">
                    <h3>Persoon ${index + 1}: ${member.full_name}</h3>

                    <article class="member-result">
                        <h4>Box 1 - Werk en woning</h4>
                        <div class="totals-row"><span>Bruto inkomen Box 1</span><strong>${this.currency(member.box1.gross_income)}</strong></div>
                        <div class="totals-row"><span>Eigenwoningforfait (bijtelling)</span><strong>${this.currency(member.box1.eigenwoningforfait)}</strong></div>
                        <div class="totals-row"><span>Aftrek geen/kleine eigenwoningschuld</span><strong>-${this.currency(member.box1.aftrek_geen_of_kleine_eigenwoningschuld)}</strong></div>
                        <div class="totals-row"><span>Belastbaar inkomen Box 1</span><strong>${this.currency(member.box1.taxable_income)}</strong></div>
                    </article>

                    <article class="member-result">
                        <h4>Berekening inkomstenbelasting en premie volksverzekeringen</h4>
                        <div class="totals-row"><span>Belasting Box 1</span><strong>${this.currency(member.box1.tax)}</strong></div>
                        ${brackets ? `<ul>${brackets}</ul>` : ""}
                        <div class="totals-row"><span>Grondslag sparen en beleggen (toegedeeld)</span><strong>${this.currency(member.box3.grondslag_sparen_beleggen)}</strong></div>
                        <div class="totals-row"><span>Aandeel (${(member.box3.partner_share_percentage || 0).toFixed(2)}%)</span><strong>${this.currency(member.box3.fictief_rendement_partner)}</strong></div>
                        <div class="totals-row"><span>Vrijstelling groene beleggingen</span><strong>-${this.currency(member.box3.vrijstelling_groene_beleggingen)}</strong></div>
                        <div class="totals-row"><span>Belastbaar inkomen Box 3 (toegedeeld)</span><strong>${this.currency(member.box3.taxable_income)}</strong></div>
                        <div class="totals-row"><span>Belasting Box 3</span><strong>${this.currency(member.box3.tax_before_foreign_dividend || member.box3.tax)}</strong></div>
                        <div class="totals-row"><span>Verrekening buitenlandse bronbelasting Box 3</span><strong>-${this.currency(member.box3.foreign_dividend_tax_credit_applied || 0)}</strong></div>
                        <div class="totals-row"><span>Premie AOW</span><strong>${this.currency(member.premiums.aow)}</strong></div>
                        <div class="totals-row"><span>Premie ANW</span><strong>${this.currency(member.premiums.anw)}</strong></div>
                        <div class="totals-row"><span>Premie Wlz</span><strong>${this.currency(member.premiums.wlz)}</strong></div>
                        <div class="totals-row"><span>Subtotaal belasting en premies</span><strong>${this.currency(grossTaxAndPremiums)}</strong></div>

                        <h4>Heffingskortingen</h4>
                        ${creditItems}
                        <div class="totals-row"><span>Totaal heffingskortingen</span><strong>-${this.currency(member.box1.credits.total)}</strong></div>

                        <h4>Voorheffingen</h4>
                        <div class="totals-row"><span>Ingehouden loonheffing</span><strong>-${this.currency(member.prepayments.wage_withholding)}</strong></div>
                        <div class="totals-row"><span>Ingehouden dividendbelasting</span><strong>-${this.currency(member.prepayments.dividend_withholding)}</strong></div>
                        <div class="totals-row"><span>Totaal voorheffingen</span><strong>-${this.currency(member.prepayments.total)}</strong></div>

                        <div class="totals-row final"><span>Eindafrekening ${member.full_name}</span><strong>${this.currency(member.settlement.net_settlement)}</strong></div>
                    </article>
                </section>
            `;
        }).join("");
        document.getElementById("personsResults").innerHTML = personsResults;

        document.getElementById("box2Income").textContent = this.currency(box2.total_taxable_income);
        document.getElementById("box2Rate").textContent = `${box2.tax_rate.toFixed(2)}%`;
        document.getElementById("box2Tax").textContent = this.currency(box2.total_tax);

        document.getElementById("box3NetAssets").textContent = this.currency(box3.total_net_assets);
        document.getElementById("box3DebtIncomePost").textContent = this.currency(box3.debt_negative_income_post);
        document.getElementById("box3TaxFree").textContent = this.currency(box3.tax_free_assets);
        document.getElementById("box3Correction").textContent = `${(box3.correction_factor * 100).toFixed(2)}%`;
        document.getElementById("box3Income").textContent = this.currency(box3.corrected_deemed_return);
        document.getElementById("box3Tax").textContent = this.currency(box3.total_tax);

        const allocationRows = result.members.map((member) => {
            return `<div class="totals-row"><span>Toegedeelde grondslag Box 3 ${member.full_name}</span><strong>${this.currency(box3.allocation && box3.allocation[member.member_id] || 0)}</strong></div>`;
        }).join("");
        document.getElementById("box3Allocation").innerHTML = allocationRows;

        // Overzicht: per person summary without duplication
        const summaryOverviewHtml = result.members.map((member) => {
            return `
                <div class="totals-row"><span>Te betalen inkomstenbelasting en premie ${member.full_name}</span><strong>${this.currency(member.settlement.net_settlement)}</strong></div>
            `;
        }).join("");
        document.getElementById("summaryOverview").innerHTML = summaryOverviewHtml;

        const combinedTax = result.members.reduce((sum, member) => {
            return sum + Number(member.settlement.net_settlement || 0);
        }, 0);
        document.getElementById("summaryCombinedTax").textContent = this.currency(combinedTax);

    },

    currency(value) {
        return new Intl.NumberFormat("nl-NL", {
            style: "currency",
            currency: "EUR",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(Number(value || 0));
    },
};

document.addEventListener("DOMContentLoaded", () => app.init());
