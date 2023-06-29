import React, { useState } from "react";
import api from "./api";
import QRCode from "react-qr-code";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import { toast } from "react-toastify";


const UrlShortenerForm = () => {
  const [original_url, setOriginalUrl] = useState("");
  const [short_code, setCustomShortcode] = useState("");
  const [shortenedUrl, setShortenedUrl] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await api.post("/shorten", {
        original_url,
        short_code,
      });
      const { data } = response;
      const rawData = data.shortened_url;
      const strippedData = rawData.replace("https://www.", "");
      setShortenedUrl(strippedData);

      // Handle the response
      toast.success("Url shortened successfully");
      setOriginalUrl("");
      setCustomShortcode("");
    } catch (error) {
      // Handle the error

      toast.error("Custom shortcode already taken");

      console.error(error);
    }
  };

  const handleCopyClick = () => {
    navigator.clipboard.writeText(shortenedUrl);
    toast.success("Url copied to clipboard");
  };

  return (

    <Container className="wrapper text-center">
      {shortenedUrl ? (
        <Row>
        
          <Col>
          <div className= "col-12 qrx">
              <QRCode value={shortenedUrl} fgColor="seagreen" />
              <p class="mt-2">Scan to copy</p>
              <div className="copy-box">
                <input
                  type="text"
                  className="copy-input form-control col-3"
                  id="myGeneratedLink"
                  value={shortenedUrl}
                  readOnly
                />
                <div className="input-group-append">
                  <button
                    className="btn btn-outline-primary"
                    type="button"
                    onClick={handleCopyClick}
                  >
                    Copy
                  </button>
                 
                </div>
              </div>
            </div>
          </Col>
          </Row>
      ):(
        <Row>
        {/* <Col className='col-2'></Col>  */}
        <Col className="">
          <form onSubmit={handleSubmit}>
            <div className="inputField">
              <h2>Shorten URL</h2>
              <div className="mb-3">
                <input
                  type="url"
                  value={original_url}
                  onChange={(e) => setOriginalUrl(e.target.value)}
                  className="form-control"
                  id="url"
                  placeholder="Paste url to shorten"
                />
              </div>
              <div className="mb-3">
                <input
                  type="custom shortcode"
                  value={short_code}
                  onChange={(e) => setCustomShortcode(e.target.value)}
                  className="form-control"
                  id="Custom shortcode"
                  placeholder="Custom shortcode"
                />
              </div>

              <button
                type="button"
                className="btn btn-outline-primary"
                onClick={handleSubmit}
              >
                Shorten
              </button>
            </div>
          </form>
          </Col>
      </Row>
      )}
      </Container>
  )
};

export default UrlShortenerForm;
