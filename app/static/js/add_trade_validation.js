const form = document.querySelector("form[name='trade_form']");
const entryPrices = document.getElementById("entry_prices");
const entryContracts = document.getElementById("entry_contracts");
const exitPrices = document.getElementById("exit_prices");
const exitContracts = document.getElementById("exit_contracts");
const entryPricesError = document.getElementById("entry_prices_error");
const entryContractsError = document.getElementById("entry_contracts_error");
const exitPricesError = document.getElementById("exit_prices_error");
const exitContractsError = document.getElementById("exit_contracts_error");

form.addEventListener("submit", (e) => {
  let isValid = true;

  // Validate entry prices
  if (!/^\d+(\.\d+)?(,\d+(\.\d+)?)*$/.test(entryPrices.value)) {
    e.preventDefault();
    entryPricesError.classList.remove("d-none");
    isValid = false;
  } else {
    entryPricesError.classList.add("d-none");
  }

  // Validate entry contracts
  if (!/^\d+(,\d+)*$/.test(entryContracts.value)) {
    e.preventDefault();
    entryContractsError.classList.remove("d-none");
    isValid = false;
  } else {
    entryContractsError.classList.add("d-none");
  }

  // Validate exit prices
  if (!/^\d+(\.\d+)?(,\d+(\.\d+)?)*$/.test(exitPrices.value)) {
    e.preventDefault();
    exitPricesError.classList.remove("d-none");
    isValid = false;
  } else {
    exitPricesError.classList.add("d-none");
  }

  // Validate exit contracts
  if (!/^\d+(,\d+)*$/.test(exitContracts.value)) {
    e.preventDefault();
    exitContractsError.classList.remove("d-none");
    isValid = false;
  } else {
    exitContractsError.classList.add("d-none");
  }

  // Validate exit contracts total
  const entryContractsTotal = entryContracts.value
    .split(",")
    .reduce((acc, curr) => acc + parseInt(curr), 0);
  const exitContractsTotal = exitContracts.value
    .split(",")
    .reduce((acc, curr) => acc + parseInt(curr), 0);
  if (entryContractsTotal !== exitContractsTotal) {
    e.preventDefault();
    exitContractsError.classList.remove("d-none");
    isValid = false;
  } else {
    exitContractsError.classList.add("d-none");
  }
});
