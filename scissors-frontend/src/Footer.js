import React from "react";

const Footer = () => {
  const today = new Date();
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
                <a class="social-icons" href="https://github.com/spartan124" target="_blank" rel="noreferrer"><ion-icon name="logo-github"></ion-icon> Github</a>
                </li>
              
              </p>
              <p>
                <li>
                  <a class="social-icons" href="https://twitter.com/jer_ryO" target="_blank" rel="noreferrer"><ion-icon name="logo-twitter"></ion-icon> Twitter</a>
                </li>
              </p>
              <p>
                <li>
                  <a class="social-icons" href="https://www.linkedin.com/in/jerrylyte" target="_blank" rel="noreferrer"> <ion-icon name="logo-linkedin"></ion-icon> LinkedIn</a>
                </li>
              </p>
            </ul>
          </div>
        </div>
        <div className="row">
          <div className="col-12">
            <p>
            &copy; {today.getFullYear()} Jerrylyte • Built with Flask, React & Postgres
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
