use alloy::providers::{Provider, ProviderBuilder};
use alloy::rpc::types::BlockNumberOrTag;
use arrow::array::{StringBuilder, UInt64Builder};
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;
use futures::stream::{self, StreamExt};
use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use std::sync::Arc;
// use url::Url;

// --- PYTHON PUBLIC INTERFACE ---

/// Fetches a single Ethereum block via RPC and writes it to a local Parquet file
#[pyfunction]
fn fetch_block_arrow(
    py: Python<'_>,
    rpc_url: String,
    block_number: u64,
    output_path: String,
) -> PyResult<&PyAny> {
    future_into_py(py, async move {
        process_block(rpc_url, block_number, output_path)
            .await
            .map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                    "Error processing block: {}",
                    e
                ))
            })
    })
}

/// Fetches a range of blocks and writes them to Parquet files
#[pyfunction]
fn extract_range(
    py: Python<'_>,
    rpc_url: String,
    start: u64,
    end: u64,
    output_dir: String,
    concurrency: usize,
) -> PyResult<&PyAny> {
    future_into_py(py, async move {
        let stream = stream::iter(start..=end)
            .map(|block_number| {
                let url = rpc_url.clone();
                let dir = output_dir.clone();

                async move { process_block(url, block_number, dir).await }
            })
            .buffer_unordered(concurrency); // Limit concurrency

        // Collect results
        let mut success_count = 0;
        let results = stream.collect::<Vec<_>>().await;

        for result in results {
            match result {
                Ok(_) => success_count += 1,
                Err(e) => println!("Error: {}", e),
            }
        }
        Ok(format!("Processed {} blocks successfully.", success_count))
    })
}

/// Returns the latest block number from the connected RPC node.
#[pyfunction]
fn get_latest_block(py: Python<'_>, rpc_url: String) -> PyResult<&PyAny> {
    future_into_py(py, async move {
        // Parse the URL
        // let valid_url = Url::parse(&rpc_url).map_err(|e| {
        //     PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid URL: {}", e))
        // })?;

       // Build the Provider
        let provider = ProviderBuilder::new().on_builtin(&rpc_url).await.map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to connect: {}", e))
        })?;
        
        // let client = ReqwestClient::new();
        // let transport = Http::with_client(client, valid_url);
        // let rpc_client = alloy::rpc::client::RpcClient::new(transport, true);
        // let provider = RootProvider::new(rpc_client);

        // Fetch the block number
        let block_number = provider.get_block_number().await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to get block number: {}",
                e
            ))
        })?;

        // Return the block number as u64
        Ok(block_number)
    })
}


// --- MODULE REGISTRATION ---
#[pymodule]
fn eth_lake(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_latest_block, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_block_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(extract_range, m)?)?;
    Ok(())
}

// --- HELPERS ---
/// Core logic: Connects, fetches, transforms to Arrow, and writes to Parquet
async fn process_block(
    rpc_url: String,
    block_number: u64,
    output_dir: String,
) -> anyhow::Result<String> {
    
    // -- SETUP CONNECTION --
    let provider = ProviderBuilder::new().on_builtin(&rpc_url).await?;
    let alloy_block_number = BlockNumberOrTag::Number(block_number);
    
    // let valid_url = Url::parse(&rpc_url)?;
    // let client = ReqwestClient::new();
    // let transport = Http::with_client(client, valid_url);
    // let rpc_client = alloy::rpc::client::RpcClient::new(transport, true);
    // let provider = RootProvider::new(rpc_client);

    // -- FETCH BLOCK DATA --
    let block_data = provider
        .get_block_by_number(alloy_block_number, true)
        .await
        .map_err(|e| anyhow::anyhow!("Network error:{}", e))?
        .ok_or_else(|| anyhow::anyhow!("Block not found!"))?;

    // -- DEFINE SCHEMA & BUILDERS --
    let schema = Schema::new(vec![
        Field::new("number", DataType::UInt64, false),
        Field::new("hash", DataType::Utf8, false),
        Field::new("parent_hash", DataType::Utf8, false),
    ]);

    let mut number_builder = UInt64Builder::new();
    let mut hash_builder = StringBuilder::new();
    let mut parent_builder = StringBuilder::new();

    // -- POPULATE BUILDERS --
    number_builder.append_value(block_data.header.number.unwrap_or_default());
    hash_builder.append_value(
        block_data
            .header
            .hash
            .map(|h| h.to_string())
            .unwrap_or_default(),
    );
    parent_builder.append_value(block_data.header.parent_hash.to_string());

    // -- CREATE RECORD BATCH --
    let batch = RecordBatch::try_new(
        Arc::new(schema),
        vec![
            Arc::new(number_builder.finish()),
            Arc::new(hash_builder.finish()),
            Arc::new(parent_builder.finish()),
        ],
    )?;

    // -- WRITE TO PARQUET --
    let file_name = format!("{}/block_{}.parquet", output_dir, block_number);
    let file = std::fs::File::create(&file_name)?;
    let mut writer =
        parquet::arrow::arrow_writer::ArrowWriter::try_new(file, batch.schema(), None)?;

    writer.write(&batch)?;
    writer.close()?;

    Ok(file_name)
}

// --- TESTS ---
#[cfg(test)]
mod tests {
    use super::*;

    // To ensure types are wired up correctly
    #[test]
    fn test_schema_definition() {
        let schema = Schema::new(vec![
            Field::new("number", DataType::UInt64, false),
            Field::new("hash", DataType::Utf8, false),
            Field::new("parent_hash", DataType::Utf8, false),
        ]);

        assert_eq!(schema.fields().len(), 3);
        assert_eq!(schema.field(0).name(), "number");
        assert_eq!(schema.field(1).name(), "hash");
        assert_eq!(schema.field(2).name(), "parent_hash");
    }
}