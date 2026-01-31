"""
UML Class Diagram Generator for EconModel from models.py
This script generates a simplified UML diagram showing the structure and relationships
of the EconModel class and its associated agent classes with common functions.
"""


def generate_uml_diagram():
    uml_content = """
@startuml EconModel_Common_Functions_Diagram

!theme plain
skinparam backgroundColor White
skinparam classBackgroundColor LightYellow
skinparam classBorderColor DarkBlue
skinparam packageBackgroundColor LightBlue

package "Economic Simulation Model" {
    
    class EconModel {
        <<Main Model>>
        + GDP: float
        + gini: float
        + covidState: bool
        + lockdown: bool
        + consumer_agents: AgentList
        + bank_agents: AgentList
        + firms: AgentList
        + climateModule: AgentList
        --
        + setup(): void
        + step(): void
        + initiate_step(): void
        + stepwise_forecast(): void
        + stepwise_produce(): void
        + stepwise_after_production(): void
        + stepwise_termination(): void
        + update(): void
        --
        - _csf_forecast_demand(): void
        - _csf_transaction(): void
        - _cpf_forecast_demand(): void
        - _cpf_transaction(): void
        - _energy_demand(): void
        - _hire(): void
        - _propagate_covid(): void
        - _carbon_tax_policy(): void
        - _fiscal_policy(): void
    }

    class Consumer {
        <<Agent>>
        + consumerType: str
        + deposit: float
        + wage: float
        + employed: bool
        + covidState: dict
        --
        + getWage(): float
        + getIncome(): float
        + getConsumption(): float
        + get_desired_consumption(): float
        + isEmployed(): bool
        + isWorker(): bool
        + getCovidStateAttr(): any
        + setConsumerType(): void
        + setAgeGroup(): void
        + update_deposit(): void
        + update_wealth(): void
        + desired_C(): void
        + receiveHiring(): void
    }

    class Bank {
        <<Agent>>
        + loans: float
        + equity: float
        + deposits: float
        + NPL: float
        + profit: float
        --
        + reset_bank(): void
        + sommaW(): void
    }

    class Government {
        <<Agent>>
        + budget: float
        + fiscal: bool
        --
        + update_budget(): void
        + E_Gov(): float
        + UE_Gov(): float
    }

    abstract class Firm {
        <<Abstract Agent>>
        + useEnergy: str
        + capital: float
        + price: float
        + net_profit: float
        + lockdown: bool
        + soldProducts: float
        + workersList: list
        --
        + getPrice(): float
        + getSoldProducts(): float
        + getUseEnergy(): str
        + get_capital(): float
        + get_actual_production(): float
        + get_capital_demand(): float
        + getNetWorth(): float
        + getOwnerIncome(): float
        + produce(): void
        + price_setting(): void
        + compute_net_profit(): void
        + update_capital_growth(): void
        + calculate_input_demand(): void
        + production_budgeting(): void
        + setLockDown(): void
        + setBankruptcy(): void
    }

    class ConsumerGoodsFirm {
        <<Consumer Goods>>
        + market_share: float
        + profit_margin: float
        + loanObtained: float
        --
        + prepareForecast(): void
        + set_aggregate_demand(): void
        + updateSoldProducts(): void
        + get_average_production_cost(): float
        + update_sale_record(): void
    }

    class CapitalGoodsFirm {
        <<Capital Goods>>
        + capital_purchase: float
        + loanObtained: float
        --
        + prepareForecast(): void
        + set_aggregate_demand(): void
        + set_capital_investment(): void
        + set_capital_price(): void
        + updateSoldProducts(): void
    }

    class GreenEnergyFirm {
        <<Green Energy>>
        + energy_demand: float
        --
        + set_energy_demand(): void
        + get_capital_investment(): float
    }

    class BrownEnergyFirm {
        <<Brown Energy>>
        + energy_demand: float
        --
        + set_energy_demand(): void
        + get_capital_investment(): float
    }

    class Climate {
        <<Climate System>>
        + CO2: float
        + T: float
        + EM: float
        
        --
        + initGDP(): void
        + progress(): void
        + initAggregatedIncome(): void
        + climate_damage_household(): list
        + climate_damage_firm(): list
    }

    class "ap.Model" as ApModel {
        <<Framework>>
        + t: int
        + p: Parameters
        --
        + step(): void
        + record(): void
    }

    class "ap.AgentList" as AgentList {
        <<Framework>>
        --
        + select(): AgentList
        + getWage(): list
        + getIncome(): list
        + getConsumption(): list
        + isEmployed(): list
    }
}

' Main inheritance
ApModel <|-- EconModel

' Firm hierarchy
Firm <|-- ConsumerGoodsFirm
Firm <|-- CapitalGoodsFirm
Firm <|-- GreenEnergyFirm
Firm <|-- BrownEnergyFirm

' Composition (EconModel contains agents)
EconModel *-- "many" Consumer
EconModel *-- "1" Bank
EconModel *-- "1" Government
EconModel *-- "many" ConsumerGoodsFirm
EconModel *-- "many" CapitalGoodsFirm
EconModel *-- "1" GreenEnergyFirm
EconModel *-- "1" BrownEnergyFirm
EconModel *-- "0..1" Climate

' Framework usage
EconModel --> AgentList : uses
Consumer --> AgentList : grouped in
Firm --> AgentList : grouped in

' Key interactions
Consumer --> Firm : works for
Bank --> Firm : lends to
Government --> EconModel : regulates
Climate --> Firm : affects

note top of EconModel
    Main simulation controller with stepwise execution:
    1. stepwise_forecast() - agents forecast demand
    2. stepwise_produce() - firms produce goods
    3. stepwise_after_production() - transactions & accounting
    4. stepwise_termination() - cleanup & bankruptcy
end note

note bottom of Firm
    Four firm types with common methods:
    - Consumer/Capital goods firms: market transactions
    - Energy firms: provide power to other firms
    - All inherit production, pricing, bankruptcy logic
end note

note right of Consumer
    Agent types: workers, capitalists,
    green/brown energy owners
    Handles employment, consumption,
    COVID states, wealth updates
end note

@enduml
"""
    return uml_content


def save_uml_diagram():
    """Save the UML diagram to a file"""
    uml_content = generate_uml_diagram()

    with open("econmodel_uml_diagram_common_functions.puml", "w") as f:
        f.write(uml_content)

    print(
        "UML diagram with common functions saved to 'econmodel_uml_diagram_common_functions.puml'"
    )
    print("\nTo generate the diagram image:")
    print("1. Install PlantUML: pip install plantuml")
    print("2. Run: python -m plantuml econmodel_uml_diagram_common_functions.puml")
    print("3. Or use online PlantUML editor: http://www.plantuml.com/plantuml/uml/")

    return uml_content


if __name__ == "__main__":
    uml_content = save_uml_diagram()
    print("\nUML PlantUML Code with Common Functions:")
    print("=" * 50)
    print(uml_content)
