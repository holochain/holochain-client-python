use fixture_integrity::*;
use hdk::prelude::*;

/// Create a `Fixture` entry, link it under the `all_fixtures` path, and return
/// the created `Record`. Exercises `Record`/`Action`/`Entry` decoding.
#[hdk_extern]
pub fn create_fixture(fixture: Fixture) -> ExternResult<Record> {
    let action_hash = create_entry(&EntryTypes::Fixture(fixture.clone()))?;
    let record = get(action_hash.clone(), GetOptions::default())?.ok_or(wasm_error!(
        WasmErrorInner::Guest("could not find the newly created Fixture".into())
    ))?;
    let path = Path::from("all_fixtures");
    create_link(
        path.path_entry_hash()?,
        action_hash,
        LinkTypes::AllFixtures,
        (),
    )?;
    Ok(record)
}

/// Fetch a `Fixture` record by its action hash.
#[hdk_extern]
pub fn get_fixture(action_hash: ActionHash) -> ExternResult<Option<Record>> {
    get(action_hash, GetOptions::default())
}

/// List all links from the `all_fixtures` path.
#[hdk_extern]
pub fn get_all_fixtures(_: ()) -> ExternResult<Vec<Link>> {
    let path = Path::from("all_fixtures");
    get_links(
        LinkQuery::try_new(path.path_entry_hash()?, LinkTypes::AllFixtures)?,
        GetStrategy::default(),
    )
}

/// Echo the input back. The simplest possible round-trip.
#[hdk_extern]
pub fn echo(value: String) -> ExternResult<String> {
    Ok(value)
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(tag = "type")]
pub enum Signal {
    Echo { value: String },
}

/// Emit an app signal so the client can exercise signal delivery.
#[hdk_extern]
pub fn emit(value: String) -> ExternResult<()> {
    emit_signal(Signal::Echo { value })?;
    Ok(())
}
