use hdk::prelude::*;
use fixture_integrity::*;
#[hdk_extern]
pub fn create_fixture(fixture: Fixture) -> ExternResult<Record> {
    let fixture_hash = create_entry(&EntryTypes::Fixture(fixture.clone()))?;
    let record = get(fixture_hash.clone(), GetOptions::default())?
        .ok_or(
            wasm_error!(
                WasmErrorInner::Guest(String::from("Could not find the newly created Fixture"))
            ),
        )?;
    let path = Path::from("all_fixtures");
    create_link(
        path.path_entry_hash()?,
        fixture_hash.clone(),
        LinkTypes::AllFixtures,
        (),
    )?;
    Ok(record)
}
#[hdk_extern]
pub fn get_latest_fixture(
    original_fixture_hash: ActionHash,
) -> ExternResult<Option<Record>> {
    let links = get_links(
        original_fixture_hash.clone(),
        LinkTypes::FixtureUpdates,
        None,
    )?;
    let latest_link = links
        .into_iter()
        .max_by(|link_a, link_b| link_a.timestamp.cmp(&link_b.timestamp));
    let latest_fixture_hash = match latest_link {
        Some(link) => {
            link.target
                .clone()
                .into_action_hash()
                .ok_or(
                    wasm_error!(
                        WasmErrorInner::Guest(String::from("No action hash associated with link"))
                    ),
                )?
        }
        None => original_fixture_hash.clone(),
    };
    get(latest_fixture_hash, GetOptions::default())
}
#[hdk_extern]
pub fn get_original_fixture(
    original_fixture_hash: ActionHash,
) -> ExternResult<Option<Record>> {
    let Some(details) = get_details(original_fixture_hash, GetOptions::default())? else {
        return Ok(None);
    };
    match details {
        Details::Record(details) => Ok(Some(details.record)),
        _ => {
            Err(
                wasm_error!(
                    WasmErrorInner::Guest(String::from("Malformed get details response"))
                ),
            )
        }
    }
}
#[hdk_extern]
pub fn get_all_revisions_for_fixture(
    original_fixture_hash: ActionHash,
) -> ExternResult<Vec<Record>> {
    let Some(original_record) = get_original_fixture(original_fixture_hash.clone())?
    else {
        return Ok(vec![]);
    };
    let links = get_links(
        original_fixture_hash.clone(),
        LinkTypes::FixtureUpdates,
        None,
    )?;
    let get_input: Vec<GetInput> = links
        .into_iter()
        .map(|link| Ok(
            GetInput::new(
                link
                    .target
                    .into_action_hash()
                    .ok_or(
                        wasm_error!(
                            WasmErrorInner::Guest(String::from("No action hash associated with link"))
                        ),
                    )?
                    .into(),
                GetOptions::default(),
            ),
        ))
        .collect::<ExternResult<Vec<GetInput>>>()?;
    let records = HDK.with(|hdk| hdk.borrow().get(get_input))?;
    let mut records: Vec<Record> = records.into_iter().filter_map(|r| r).collect();
    records.insert(0, original_record);
    Ok(records)
}
#[derive(Serialize, Deserialize, Debug)]
pub struct UpdateFixtureInput {
    pub original_fixture_hash: ActionHash,
    pub previous_fixture_hash: ActionHash,
    pub updated_fixture: Fixture,
}
#[hdk_extern]
pub fn update_fixture(input: UpdateFixtureInput) -> ExternResult<Record> {
    let updated_fixture_hash = update_entry(
        input.previous_fixture_hash.clone(),
        &input.updated_fixture,
    )?;
    create_link(
        input.original_fixture_hash.clone(),
        updated_fixture_hash.clone(),
        LinkTypes::FixtureUpdates,
        (),
    )?;
    let record = get(updated_fixture_hash.clone(), GetOptions::default())?
        .ok_or(
            wasm_error!(
                WasmErrorInner::Guest(String::from("Could not find the newly updated Fixture"))
            ),
        )?;
    Ok(record)
}
#[hdk_extern]
pub fn delete_fixture(original_fixture_hash: ActionHash) -> ExternResult<ActionHash> {
    let details = get_details(original_fixture_hash.clone(), GetOptions::default())?
        .ok_or(
            wasm_error!(
                WasmErrorInner::Guest(String::from("{pascal_entry_def_name} not found"))
            ),
        )?;
    match details {
        Details::Record(details) => Ok(details.record),
        _ => {
            Err(
                wasm_error!(
                    WasmErrorInner::Guest(String::from("Malformed get details response"))
                ),
            )
        }
    }?;
    let path = Path::from("all_fixtures");
    let links = get_links(path.path_entry_hash()?, LinkTypes::AllFixtures, None)?;
    for link in links {
        if let Some(hash) = link.target.into_action_hash() {
            if hash.eq(&original_fixture_hash) {
                delete_link(link.create_link_hash)?;
            }
        }
    }
    delete_entry(original_fixture_hash)
}
#[hdk_extern]
pub fn get_all_deletes_for_fixture(
    original_fixture_hash: ActionHash,
) -> ExternResult<Option<Vec<SignedActionHashed>>> {
    let Some(details) = get_details(original_fixture_hash, GetOptions::default())? else {
        return Ok(None);
    };
    match details {
        Details::Entry(_) => {
            Err(wasm_error!(WasmErrorInner::Guest("Malformed details".into())))
        }
        Details::Record(record_details) => Ok(Some(record_details.deletes)),
    }
}
#[hdk_extern]
pub fn get_oldest_delete_for_fixture(
    original_fixture_hash: ActionHash,
) -> ExternResult<Option<SignedActionHashed>> {
    let Some(mut deletes) = get_all_deletes_for_fixture(original_fixture_hash)? else {
        return Ok(None);
    };
    deletes
        .sort_by(|delete_a, delete_b| {
            delete_a.action().timestamp().cmp(&delete_b.action().timestamp())
        });
    Ok(deletes.first().cloned())
}
