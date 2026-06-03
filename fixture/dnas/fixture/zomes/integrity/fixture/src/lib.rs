use hdi::prelude::*;

/// A trivial app entry used by the client test-suite to exercise zome calls
/// and `Record`/`Action`/`Entry` deserialization.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Fixture {
    pub value: String,
}

#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    #[entry_type(visibility = "public")]
    Fixture(Fixture),
}

#[hdk_link_types]
pub enum LinkTypes {
    AllFixtures,
    FixtureUpdates,
}

#[hdk_extern]
pub fn genesis_self_check(_: GenesisSelfCheckData) -> ExternResult<ValidateCallbackResult> {
    Ok(ValidateCallbackResult::Valid)
}

#[hdk_extern]
pub fn validate(_op: Op) -> ExternResult<ValidateCallbackResult> {
    Ok(ValidateCallbackResult::Valid)
}
