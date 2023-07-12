import React from "react";

const Footer = () => {
  return (
    <footer>
      <div class="container text-center text-white pt-5 pb-5 mt-5">
        <div class="row">
          <div class="col-12 col-md-6 columnContent">
            <h2 class="mb-3">Scix</h2>
            <p>
              Scix is a url shortening service powered by a REST API backend. Features include url shortening and tracking of shortened links.
            </p>
          </div>

          <div class="col-12 col-md-6 columnContent">
            <h2 class="mb-3">Quick Links</h2>
            <ul>
              <p>
                <li>
                <a href="https://www.github.com/spartan124">Github</a>
                </li>
              
              </p>
              <p>
                <li>
                  <a href="https://www.twitter.com/jer_ryO">Twitter</a>
                </li>
              </p>
              <p>
                <li>
                  <a href="https://www.linkedin.com/in/jerrylyte">LinkedIn</a>
                </li>
              </p>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
