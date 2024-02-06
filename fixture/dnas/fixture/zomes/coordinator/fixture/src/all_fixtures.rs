use hdk::prelude::*;
use fixture_integrity::*;
#[hdk_extern]
pub fn get_all_fixtures(_: ()) -> ExternResult<Vec<Link>> {
    let path = Path::from("all_fixtures");
    get_links(path.path_entry_hash()?, LinkTypes::AllFixtures, None)
}
